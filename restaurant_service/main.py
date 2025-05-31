# -------- restaurant.py --------
from fastapi import FastAPI, HTTPException, status
from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.fastapi import register_tortoise
from pydantic import BaseModel
import httpx
from typing import List, Optional

app = FastAPI()

delivery_agent_service_client = httpx.AsyncClient(base_url="http://delivery_agent_service:8002", timeout=5.0)

# --- TORTISE ORM MODELS ---

class Restaurant(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    online = fields.BooleanField(default=True)

class MenuItem(Model):
    id = fields.IntField(pk=True)
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='menu_items')
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    available = fields.BooleanField(default=True)

class Order(Model):
    id = fields.IntField(pk=True)
    restaurant = fields.ForeignKeyField('models.Restaurant', related_name='orders')
    user_id = fields.IntField()
    status = fields.CharField(max_length=50)
    items = fields.JSONField()
    assigned_agent_id = fields.IntField(null=True)
    restaurant_rating = fields.IntField(null=True)
    agent_rating = fields.IntField(null=True)

# --- PYDANTIC MODELS ---

class RestaurantIn(BaseModel):
    name: str
    online: bool = True
    class Config: 
        from_attributes = True

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    online: Optional[bool] = None
    class Config:
        from_attributes = True

class MenuItemIn(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    available: bool = True
    class Config: 
        from_attributes = True

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None
    class Config:
        from_attributes = True

class OrderIn(BaseModel):
    user_id: int
    restaurant_id: int
    items: List[str]
    class Config: 
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str
    class Config:
        from_attributes = True

class OrderRatingUpdate(BaseModel):
    restaurant_rating: int
    agent_rating: int
    class Config: 
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    restaurant_id: int 
    user_id: int
    status: str
    items: List[str]
    assigned_agent_id: Optional[int] = None
    restaurant_rating: Optional[int] = None
    agent_rating: Optional[int] = None

    class Config:
        from_attributes = True 

# --- API ENDPOINTS ---

@app.get("/restaurants/available", response_model=List[RestaurantIn]) 
async def list_online():
    return await Restaurant.filter(online=True).all()

@app.post("/restaurants", response_model=RestaurantIn, status_code=status.HTTP_201_CREATED) 
async def add_restaurant(r_in: RestaurantIn):
    return await Restaurant.create(**r_in.model_dump())

@app.put("/restaurants/{restaurant_id}", response_model=RestaurantIn)
async def update_restaurant(restaurant_id: int, r_update: RestaurantUpdate):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    update_data = r_update.model_dump(exclude_unset=True)
    if update_data:
        await restaurant.update_from_dict(update_data).save()
    return restaurant

@app.post("/restaurants/{restaurant_id}/menu", response_model=MenuItemIn, status_code=status.HTTP_201_CREATED) 
async def add_menu_item(restaurant_id: int, item_in: MenuItemIn):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    new_item = await MenuItem.create(restaurant=restaurant, **item_in.model_dump())
    return new_item

@app.put("/restaurants/{restaurant_id}/menu/{item_id}", response_model=MenuItemIn) 
async def update_menu_item(restaurant_id: int, item_id: int, item_update: MenuItemUpdate):
    item = await MenuItem.get_or_none(id=item_id, restaurant_id=restaurant_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found for this restaurant.")

    update_data = item_update.model_dump(exclude_unset=True)
    if update_data:
        await item.update_from_dict(update_data).save()
    return item

@app.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItemIn])
async def get_menu(restaurant_id: int):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    return await MenuItem.filter(restaurant=restaurant).all()


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderIn):
    restaurant_obj = await Restaurant.get_or_none(id=order.restaurant_id, online=True)
    if not restaurant_obj:
        raise HTTPException(status_code=404, detail="Restaurant not found or not online.")

    db_order = await Order.create(
        restaurant=restaurant_obj,
        user_id=order.user_id,
        status="pending_acceptance",
        items=order.items
    )
    return OrderResponse.from_orm(db_order) 

@app.put("/orders/{order_id}/status", response_model=OrderResponse) 
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


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_details(order_id: int):
    """
    Retrieves details for a specific order.
    Used internally by other services (e.g., delivery_agent_service).
    """
    order = await Order.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return OrderResponse.from_orm(order) 

@app.put("/orders/{order_id}/rate", response_model=OrderResponse) 
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


@app.get("/restaurants/{restaurant_id}", response_model=RestaurantIn) 
async def get_restaurant(restaurant_id: int):
    """
    Retrieves details for a specific restaurant by its ID.
    This endpoint is used by the user_service's GraphQL gateway.
    """
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    return restaurant

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok", "message": "Service is healthy"}


# --- TORTISE ORM REGISTRATION ---
register_tortoise(
    app,
    db_url="postgres://postgres:mysecretpassword@food_delivery_postgres:5432/postgres",
    modules={"models": ["main"]}, 
    generate_schemas=True,
    add_exception_handlers=True,
)

# --- SHUTDOWN EVENT ---
@app.on_event("shutdown")
async def shutdown_event():
    await delivery_agent_service_client.aclose()
