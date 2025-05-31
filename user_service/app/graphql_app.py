import strawberry
from typing import List, Optional

from .schemas import Restaurant, DeliveryAgent, Order, OrderInput
from . import services 

@strawberry.type
class Query:
    @strawberry.field
    async def get_available_restaurants(self) -> List[Restaurant]:
        """Fetches a list of all currently online restaurants."""
        return await services.fetch_available_restaurants()

    @strawberry.field
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Fetches details for a specific order by ID."""
        order = await services.fetch_order_details(order_id)
        if order:
            order.restaurant = lambda: services.get_restaurant_data(order.restaurant_id)
            order.assigned_agent = lambda: services.get_delivery_agent_data(order.assigned_agent_id)
        return order


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def rate_order(self, order_id: int, restaurant_rating: int, agent_rating: int) -> Order:
        """Submits a rating for an order and its agent/restaurant."""
        rated_order = await services.update_order_rating(order_id, restaurant_rating, agent_rating)
        rated_order.restaurant = lambda: services.get_restaurant_data(rated_order.restaurant_id)
        rated_order.assigned_agent = lambda: services.get_delivery_agent_data(rated_order.assigned_agent_id)
        return rated_order

    @strawberry.mutation
    async def place_order(self, order_data: OrderInput) -> Order:
        """Places a new order through the restaurant service."""
        new_order = await services.create_new_order(order_data.model_dump())
        new_order.restaurant = lambda: services.get_restaurant_data(new_order.restaurant_id)
        new_order.assigned_agent = lambda: services.get_delivery_agent_data(new_order.assigned_agent_id)
        return new_order

schema = strawberry.Schema(query=Query, mutation=Mutation)
