import httpx
from typing import List, Optional
from fastapi import HTTPException
from .schemas import Restaurant, DeliveryAgent, Order 

restaurant_service_client = httpx.AsyncClient(base_url="http://restaurant_service:8001", timeout=10.0)
delivery_agent_service_client = httpx.AsyncClient(base_url="http://delivery_agent_service:8002", timeout=10.0)

async def get_restaurant_data(restaurant_id: int) -> Optional[Restaurant]:
    """Fetches restaurant details from the restaurant service."""
    try:
        resp = await restaurant_service_client.get(f"/restaurants/{restaurant_id}")
        resp.raise_for_status()
        return Restaurant(**resp.json())
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        raise
    except Exception as e:
        print(f"Error fetching restaurant {restaurant_id}: {e}")
        raise

async def get_delivery_agent_data(agent_id: int) -> Optional[DeliveryAgent]:
    """Fetches delivery agent details from the delivery agent service."""
    try:
        resp = await delivery_agent_service_client.get(f"/agents/{agent_id}")
        resp.raise_for_status()
        return DeliveryAgent(**resp.json())
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        raise
    except Exception as e:
        print(f"Error fetching agent {agent_id}: {e}")
        raise

async def fetch_available_restaurants() -> List[Restaurant]:
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

async def fetch_order_details(order_id: int) -> Optional[Order]:
    """Fetches details for a specific order by ID."""
    try:
        resp = await restaurant_service_client.get(f"/orders/{order_id}")
        resp.raise_for_status()
        return Order(**resp.json())
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service: {exc.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

async def update_order_rating(order_id: int, restaurant_rating: int, agent_rating: int) -> Order:
    """Submits a rating for an order and its agent/restaurant."""
    try:
        resp = await restaurant_service_client.put(
            f"/orders/{order_id}/rate",
            json={"restaurant_rating": restaurant_rating, "agent_rating": agent_rating}
        )
        resp.raise_for_status()
        return Order(**resp.json())
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error rating order: {exc.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during rating: {str(e)}")

async def create_new_order(order_data: dict) -> Order:
    """Places a new order through the restaurant service."""
    try:
        resp = await restaurant_service_client.post("/orders", json=order_data)
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

async def close_http_clients():
    """Closes httpx clients on application shutdown."""
    await restaurant_service_client.aclose()
    await delivery_agent_service_client.aclose()
