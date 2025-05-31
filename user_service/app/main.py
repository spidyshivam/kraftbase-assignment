from fastapi import FastAPI, status
from strawberry.fastapi import GraphQLRouter

from .graphql_app import schema 
from . import services

app = FastAPI()

graphql_app_router = GraphQLRouter(schema)
app.include_router(graphql_app_router, prefix="/graphql")

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {"status": "ok", "message": "Service is healthy"}

# --- Shutdown Event for httpx clients ---
@app.on_event("shutdown")
async def shutdown_event():
    await services.close_http_clients()
