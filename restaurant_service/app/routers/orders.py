from fastapi import APIRouter, HTTPException, status
import httpx

from ..models import Order, Restaurant
from ..schemas import OrderIn, OrderStatusUpdate, OrderRatingUpdate, OrderResponse
from ..dependencies import delivery_agent_service_client 

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_in: OrderIn):
    restaurant_obj = await Restaurant.get_or_none(id=order_in.restaurant_id, online=True)
    if not restaurant_obj:
        raise HTTPException(status_code=404, detail="Restaurant not found or not online.")

    db_order = await Order.create(
        restaurant=restaurant_obj,
        user_id=order_in.user_id,
        status="pending_acceptance",
        items=order_in.items
    )
    return OrderResponse.from_orm(db_order)

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(order_id: int, status_update: OrderStatusUpdate):
    order = await Order.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    new_status = status_update.status.lower()

    if new_status == "accepted":
        if order.status != "pending_acceptance":
            raise HTTPException(status_code=400, detail=f"Order cannot be accepted from status: {order.status}")

        order.status = "accepted"
        await order.save()

        try:
            resp = await delivery_agent_service_client.post("/assign", json={"order_id": order_id})
            resp.raise_for_status()
            assignment_result = resp.json()
            assigned_agent_id = assignment_result.get("agent_id")

            order.status = "assigned_to_agent"
            order.assigned_agent_id = assigned_agent_id
            await order.save()

            return OrderResponse.from_orm(order)
        except httpx.ConnectError:
            order.status = "acceptance_failed_no_agent"
            await order.save()
            raise HTTPException(status_code=503, detail="Delivery agent service is unavailable for assignment. Order accepted but not assigned.")
        except httpx.ReadTimeout:
            order.status = "acceptance_failed_timeout"
            await order.save()
            raise HTTPException(status_code=504, detail="Delivery agent service timed out during assignment. Order accepted but not assigned.")
        except httpx.HTTPStatusError as exc:
            order.status = "acceptance_failed_agent_service_error"
            await order.save()
            if exc.response.status_code == 409 and "No available agents" in exc.response.text:
                 raise HTTPException(status_code=409, detail="No available delivery agents to assign. Order accepted but stuck.")
            raise HTTPException(status_code=exc.response.status_code, detail=f"Delivery service error during assignment: {exc.response.text}")
        except Exception as e:
            order.status = "acceptance_failed_unexpected"
            await order.save()
            raise HTTPException(status_code=500, detail=f"Unexpected error during delivery assignment: {str(e)}")

    elif new_status == "rejected":
        if order.status not in ["pending_acceptance", "accepted", "preparing"]:
            raise HTTPException(status_code=400, detail=f"Order cannot be rejected from status: {order.status}")
        order.status = "rejected"
        await order.save()
        return OrderResponse.from_orm(order)

    elif new_status in ["preparing", "ready_for_pickup", "delivered"]:
        order.status = new_status
        await order.save()
        return OrderResponse.from_orm(order)

    else:
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported order status: {new_status}")

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(order_id: int):
    """
    Retrieves details for a specific order.
    Used internally by other services (e.g., delivery_agent_service).
    """
    order = await Order.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return OrderResponse.from_orm(order)

@router.put("/{order_id}/rate", response_model=OrderResponse)
async def rate_order(order_id: int, ratings: OrderRatingUpdate):
    """
    Updates the ratings for a specific order.
    """
    order = await Order.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.status != "delivered":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must be delivered to be rated.")

    order.restaurant_rating = ratings.restaurant_rating
    order.agent_rating = ratings.agent_rating
    await order.save()
    return OrderResponse.from_orm(order)
