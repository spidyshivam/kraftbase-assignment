from fastapi import APIRouter, HTTPException, status
from typing import List

from ..models import Restaurant, MenuItem
from ..schemas import RestaurantIn, RestaurantUpdate, MenuItemIn, MenuItemUpdate

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

@router.get("/available", response_model=List[RestaurantIn])
async def list_online():
    return await Restaurant.filter(online=True).all()

@router.post("", response_model=RestaurantIn, status_code=status.HTTP_201_CREATED)
async def add_restaurant(r_in: RestaurantIn):
    return await Restaurant.create(**r_in.model_dump())

@router.put("/{restaurant_id}", response_model=RestaurantIn)
async def update_restaurant(restaurant_id: int, r_update: RestaurantUpdate):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    update_data = r_update.model_dump(exclude_unset=True)
    if update_data:
        await restaurant.update_from_dict(update_data).save()
    return restaurant

@router.post("/{restaurant_id}/menu", response_model=MenuItemIn, status_code=status.HTTP_201_CREATED)
async def add_menu_item(restaurant_id: int, item_in: MenuItemIn):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    new_item = await MenuItem.create(restaurant=restaurant, **item_in.model_dump())
    return new_item

@router.put("/{restaurant_id}/menu/{item_id}", response_model=MenuItemIn)
async def update_menu_item(restaurant_id: int, item_id: int, item_update: MenuItemUpdate):
    item = await MenuItem.get_or_none(id=item_id, restaurant_id=restaurant_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found for this restaurant.")

    update_data = item_update.model_dump(exclude_unset=True)
    if update_data:
        await item.update_from_dict(update_data).save()
    return item

@router.get("/{restaurant_id}/menu", response_model=List[MenuItemIn])
async def get_menu(restaurant_id: int):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    return await MenuItem.filter(restaurant=restaurant).all()

@router.get("/{restaurant_id}", response_model=RestaurantIn)
async def get_restaurant(restaurant_id: int):
    """
    Retrieves details for a specific restaurant by its ID.
    This endpoint is used by the user_service's GraphQL gateway.
    """
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")
    return restaurant
