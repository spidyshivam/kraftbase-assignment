from typing import List, Optional
import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List 
import httpx

app = FastAPI()

restaurant_service_client = httpx.AsyncClient(base_url="http://restaurant_service:8001", timeout=10.0)
delivery_agent_service_client = httpx.AsyncClient(base_url="http://delivery_agent_service:8002", timeout=10.0)
#restaurant_service_client = httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0)
#delivery_agent_service_client = httpx.AsyncClient(base_url="http://localhost:8002", timeout=10.0)



@strawberry.type
class Restaurant:
    id: int
    name: str
    online: bool

@strawberry.type
class DeliveryAgent:
    id: int
    name: str
    available: bool

@strawberry.type
class Order:
    id: int
    user_id: int
    restaurant_id: int  
    status: str
    items: List[str] 
    assigned_agent_id: Optional[int] = None 

    @strawberry.field
    async def restaurant(self, info) -> Optional[Restaurant]:
        try:
            resp = await restaurant_service_client.get(f"/restaurants/{self.id}") 
            resp.raise_for_status()
            return Restaurant(**resp.json())
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        except Exception as e:
            print(f"Error fetching restaurant for order {self.id}: {e}")
            raise

    @strawberry.field
    async def assigned_agent(self, info) -> Optional[DeliveryAgent]:
        try:
            order_from_restaurant_service_resp = await restaurant_service_client.get(f"/orders/{self.id}")
            order_from_restaurant_service_resp.raise_for_status()
            order_data = order_from_restaurant_service_resp.json()
            
            assigned_agent_id = order_data.get("assigned_agent_id")

            if assigned_agent_id:
                resp = await delivery_agent_service_client.get(f"/agents/{assigned_agent_id}")
                resp.raise_for_status()
                return DeliveryAgent(**resp.json())
            return None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        except Exception as e:
            print(f"Error fetching agent for order {self.id}: {e}")
            raise

@strawberry.input
class OrderInput:
    user_id: int
    restaurant_id: int
    items: List[str]




@strawberry.type
class Query:
    @strawberry.field
    async def get_available_restaurants(self) -> List[Restaurant]:
        """Fetches a list of all currently online restaurants."""
        try:
            resp = await restaurant_service_client.get("/restaurants/available")
            resp.raise_for_status()
            return [Restaurant(**r) for r in resp.json()]
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Restaurant service is unavailable.")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail="Restaurant service took too long to respond.")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    @strawberry.field
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Fetches details for a specific order by ID."""
        try:
            resp = await restaurant_service_client.get(f"/orders/{order_id}")
            resp.raise_for_status()
            return Order(**resp.json())
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None # Order not found
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")



class RatingRequest(BaseModel):
    order_id: int
    restaurant_rating: int
    agent_rating: int

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def rate_order(self, order_id: int, restaurant_rating: int, agent_rating: int) -> str:
        """Submits a rating for an order and its agent/restaurant."""
        print(f"Received rating for order {order_id}: Restaurant={restaurant_rating}, Agent={agent_rating}")
        return f"Rating received for order {order_id}"

    @strawberry.mutation
    async def place_order(self, order_data: OrderInput) -> Order: 
        """Places a new order through the restaurant service."""
        try:
            resp = await restaurant_service_client.post("/orders", json={
                "user_id": order_data.user_id,
                "restaurant_id": order_data.restaurant_id,
                "items": order_data.items
            })
            resp.raise_for_status()
            return Order(**resp.json())
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Restaurant service is unavailable to place orders.")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail="Restaurant service took too long to process order.")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.status_code, detail=f"Error placing order: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok", "message": "Service is healthy"}


schema = strawberry.Schema(query=Query, mutation=Mutation)


graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")



# --- Shutdown Event for httpx clients ---
@app.on_event("shutdown")
async def shutdown_event():
    await restaurant_service_client.aclose()
    await delivery_agent_service_client.aclose()
