from fastapi import APIRouter
from .health import router as health_router
from .scraping import router as scraping_router
from .documents import router as documents_router
from .dashboard import router as dashboard_router

# Hauptrouter erstellen
api_router = APIRouter()

# Subrouter einbinden
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(scraping_router, tags=["Scraping"])
api_router.include_router(documents_router, tags=["Documents"])
api_router.include_router(dashboard_router, tags=["Dashboard"])