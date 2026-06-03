from fastapi import APIRouter
from app.api.endpoints import security_events, alerts

api_router = APIRouter()

# Register sub-routers
api_router.include_router(
    security_events.router,
    prefix="/events",
    tags=["Security Events"]
)
api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts"]
)
