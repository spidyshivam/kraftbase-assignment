from fastapi import FastAPI, status
from tortoise.contrib.fastapi import register_tortoise

from .routers import restaurants, orders
from .dependencies import delivery_agent_service_client 

app = FastAPI()

app.include_router(restaurants.router)
app.include_router(orders.router)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok", "message": "Service is healthy"}

register_tortoise(
    app,
    db_url="postgres://postgres:mysecretpassword@food_delivery_postgres:5432/postgres",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.on_event("shutdown")
async def shutdown_event():
    await delivery_agent_service_client.aclose()
