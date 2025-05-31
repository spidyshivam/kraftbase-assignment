from fastapi import FastAPI, status
from tortoise.contrib.fastapi import register_tortoise

from app.routers import delivery
from app import external_services 

app = FastAPI(
    title="Delivery Agent Service",
    description="Manages delivery agents and their assignments.",
    version="0.1.0",
)

app.include_router(delivery.router)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok", "message": "Delivery Agent Service is healthy"}

register_tortoise(
    app,
    db_url="postgres://postgres:mysecretpassword@food_delivery_postgres:5432/postgres",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# --- Shutdown Event for httpx clients ---
@app.on_event("shutdown")
async def shutdown_event():
    """
    Closes all httpx clients gracefully when the application shuts down.
    """
    await external_services.close_http_clients()
