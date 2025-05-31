from typing import Optional, List
from tortoise.transactions import in_transaction

from app.models import DeliveryAgent
from app.schemas import DeliveryAgentIn

async def get_available_agent() -> Optional[DeliveryAgent]:
    async with in_transaction():
        agent = await DeliveryAgent.filter(available=True).first()
        return agent

async def create_delivery_agent(agent_in: DeliveryAgentIn) -> DeliveryAgent:
    new_agent = await DeliveryAgent.create(**agent_in.model_dump())
    return new_agent

async def get_delivery_agent_by_id(agent_id: int) -> Optional[DeliveryAgent]:
    agent = await DeliveryAgent.get_or_none(id=agent_id)
    return agent

async def update_agent_availability(agent: DeliveryAgent, available: bool) -> DeliveryAgent:
    agent.available = available
    await agent.save()
    return agent
