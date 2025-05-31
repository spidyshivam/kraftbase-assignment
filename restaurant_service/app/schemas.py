from pydantic import BaseModel
from typing import List, Optional

# --- Restaurant Schemas ---
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

# --- MenuItem Schemas ---
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

# --- Order Schemas ---
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
