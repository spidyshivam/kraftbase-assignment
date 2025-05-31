from typing import List, Optional
import strawberry

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
    restaurant_rating: Optional[int] = None
    agent_rating: Optional[int] = None

    @strawberry.field
    async def restaurant(self) -> Optional[Restaurant]:
        return None

    @strawberry.field
    async def assigned_agent(self) -> Optional[DeliveryAgent]:
        return None

@strawberry.input
class OrderInput:
    user_id: int
    restaurant_id: int
    items: List[str]
