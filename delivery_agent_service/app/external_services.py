import httpx
from fastapi import HTTPException, status
from typing import Dict, Any

restaurant_service_client = httpx.AsyncClient(base_url="http://restaurant_service:8001", timeout=5.0)
# restaurant_service_client = httpx.AsyncClient(base_url="http://localhost:8001", timeout=5.0)

async def get_order_details_from_restaurant_service(order_id: int) -> Dict[str, Any]:
    try:
        resp = await restaurant_service_client.get(f"/orders/{order_id}")
        resp.raise_for_status() 
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to restaurant service to verify order details.")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Restaurant service timed out during order verification.")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found in restaurant service.")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service during order verification: {exc.response.text}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error during order verification: {str(e)}")

async def update_order_status_in_restaurant_service(order_id: int, new_status: str) -> Dict[str, Any]:
    """
    Updates the status of an order in the restaurant service.
    Raises HTTPException on connection issues, timeouts, or HTTP errors.
    """
    try:
        resp = await restaurant_service_client.put(
            f"/orders/{order_id}/status",
            json={"status": new_status}
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        print(f"WARNING: Could not connect to restaurant service to update order {order_id} status.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Restaurant service unavailable for order status update.")
    except httpx.ReadTimeout:
        print(f"WARNING: Restaurant service timed out updating order {order_id} status.")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Restaurant service timed out during order status update.")
    except httpx.HTTPStatusError as exc:
        print(f"WARNING: Restaurant service returned error for order {order_id} status: {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error from restaurant service updating order status: {exc.response.text}")
    except Exception as e:
        print(f"ERROR: Unexpected error informing restaurant service for order {order_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error during order status update communication: {str(e)}")

async def close_http_clients():
    """
    Closes all httpx clients. This function should be called on application shutdown.
    """
    await restaurant_service_client.aclose()
