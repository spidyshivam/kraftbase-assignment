from fastapi import FastAPI, HTTPException
from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.fastapi import register_tortoise
from pydantic import BaseModel
from tortoise.transactions import in_transaction
import httpx

app = FastAPI()

#restaurant_service_client = httpx.AsyncClient(base_url="http://restaurant_service:8001", timeout=5.0)
restaurant_service_client = httpx.AsyncClient(base_url="http://localhost:8001", timeout=5.0)

class DeliveryAgent(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    available = fields.BooleanField(default=True)

class DeliveryAssignment(BaseModel):
    order_id: int

class DeliveryAgentIn(BaseModel):
    name: str
    available: bool = True

class DeliveryComplete(BaseModel):
    order_id: int
    agent_id: int 

@app.post("/assign")
async def assign_delivery(assignment: DeliveryAssignment):
    async with in_transaction():
        agent = await DeliveryAgent.filter(available=True).first()
        if not agent:
            raise HTTPException(status_code=409, detail="No available delivery agents at the moment.")

        agent.available = False
        await agent.save()

        return {"agent_id": agent.id, "order_id": assignment.order_id, "status": "assigned"}

@app.post("/agents")
async def add_delivery_agent(agent_in: DeliveryAgentIn):
    """
    Adds a new delivery agent to the system.
    """
    new_agent = await DeliveryAgent.create(**agent_in.model_dump())
    return new_agent

@app.post("/complete-delivery")
async def complete_delivery(delivery_complete: DeliveryComplete):
    """
    Marks a delivery as complete and updates the agent's availability.
    Also informs the restaurant service to update the order status,
    but only if the agent was actually assigned to that order.
    """
    async with in_transaction():
        agent = await DeliveryAgent.get_or_none(id=delivery_complete.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Delivery agent not found.")

        order_details = None
        try:
            resp = await restaurant_service_client.get(f"/orders/{delivery_complete.order_id}")
            resp.raise_for_status()
            order_details = resp.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Could not connect to restaurant service to verify order details.")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail="Restaurant service timed out during order verification.")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Order {delivery_complete.order_id} not found in restaurant service.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service during order verification: {exc.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error during order verification: {str(e)}")

        if order_details.get("assigned_agent_id") != delivery_complete.agent_id:
            raise HTTPException(status_code=403, detail=f"Agent {delivery_complete.agent_id} was not assigned to order {delivery_complete.order_id}.")
        
        if order_details.get("status") in ["delivered", "rejected"]:
             raise HTTPException(status_code=400, detail=f"Order {delivery_complete.order_id} is already in '{order_details.get('status')}' status and cannot be completed.")


        agent.available = True
        await agent.save()

        try:
            resp = await restaurant_service_client.put(
                f"/orders/{delivery_complete.order_id}/status",
                json={"status": "delivered"}
            )
            resp.raise_for_status()
        except httpx.ConnectError:
            print(f"WARNING: Could not connect to restaurant service to update order {delivery_complete.order_id} status.")
            raise HTTPException(status_code=503, detail="Restaurant service unavailable for order status update.")
        except httpx.ReadTimeout:
            print(f"WARNING: Restaurant service timed out updating order {delivery_complete.order_id} status.")
            raise HTTPException(status_code=504, detail="Restaurant service timed out during order status update.")
        except httpx.HTTPStatusError as exc:
            print(f"WARNING: Restaurant service returned error for order {delivery_complete.order_id} status: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service updating order status: {exc.response.text}")
        except Exception as e:
            print(f"ERROR: Unexpected error informing restaurant service for order {delivery_complete.order_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error during order status update communication: {str(e)}")

        return {
            "msg": f"Delivery for order {delivery_complete.order_id} completed successfully by agent {delivery_complete.agent_id}.",
            "agent_id": agent.id,
            "agent_available": agent.available,
            "order_status_updated": True
        }

@app.get("/agents/{agent_id}")
async def get_delivery_agent(agent_id: int):
    """
    Retrieves details for a specific delivery agent.
    Used internally by other services (e.g., user_service's GraphQL gateway).
    """
    agent = await DeliveryAgent.get_or_none(id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Delivery agent not found.")
    return agent 

register_tortoise(
    app,
    db_url="sqlite3://delivery.db",
    #db_url="postgres://postgres:mysecretpassword@localhost:5432/db.sqlite3/delivery_db",
    modules={"models": ["main"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.on_event("shutdown")
async def shutdown_event():
    await restaurant_service_client.aclose()
