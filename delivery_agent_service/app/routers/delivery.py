from fastapi import APIRouter, HTTPException, status
from tortoise.transactions import in_transaction

from app import crud
from app import external_services
from app.schemas import (
    DeliveryAssignment,
    DeliveryAgentIn,
    DeliveryAgentOut,
    DeliveryComplete,
    DeliveryCompletionResponse
)

router = APIRouter(
    prefix="/delivery", 
    tags=["Delivery Operations"] 
)

@router.post("/assign", response_model=dict) 
async def assign_delivery(assignment: DeliveryAssignment):
    async with in_transaction():
        agent = await crud.get_available_agent()
        if not agent:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No available delivery agents at the moment.")

        await crud.update_agent_availability(agent, False)

        return {"agent_id": agent.id, "order_id": assignment.order_id, "status": "assigned"}

@router.post("/agents", response_model=DeliveryAgentOut)
async def add_delivery_agent(agent_in: DeliveryAgentIn):
    new_agent = await crud.create_delivery_agent(agent_in)
    return new_agent

@router.post("/complete-delivery", response_model=DeliveryCompletionResponse)
async def complete_delivery(delivery_complete: DeliveryComplete):
      async with in_transaction():
        agent = await crud.get_delivery_agent_by_id(delivery_complete.agent_id)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found.")

        order_details = await external_services.get_order_details_from_restaurant_service(delivery_complete.order_id)

        if order_details.get("assigned_agent_id") != delivery_complete.agent_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Agent {delivery_complete.agent_id} was not assigned to order {delivery_complete.order_id}.")

        if order_details.get("status") in ["delivered", "rejected"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order {delivery_complete.order_id} is already in '{order_details.get('status')}' status and cannot be completed.")

        await crud.update_agent_availability(agent, True)

        await external_services.update_order_status_in_restaurant_service(delivery_complete.order_id, "delivered")

        return DeliveryCompletionResponse(
            msg=f"Delivery for order {delivery_complete.order_id} completed successfully by agent {delivery_complete.agent_id}.",
            agent_id=agent.id,
            agent_available=agent.available,
            order_status_updated=True
        )

@router.get("/agents/{agent_id}", response_model=DeliveryAgentOut)
async def get_delivery_agent(agent_id: int):
    agent = await crud.get_delivery_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery agent not found.")
    return agent
