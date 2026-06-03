from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # For SQLite MVP, automatically bootstrap database tables on start.
    # When using Alembic in production, migrations are run separately.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API foundation for Security Events and Incident Response Alerts.",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include the central router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get(
    "/",
    tags=["Root"],
    summary="API Root Status",
    description="Checks service availability and provides basic platform metadata."
)
def read_root():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "documentation": "/docs"
    }
