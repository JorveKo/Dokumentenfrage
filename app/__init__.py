# app/__init__.py
import logging
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

print("Initializing FastAPI application...")

# Import configuration first
from config import (
    STATIC_DIR, TEMPLATES_DIR, LOGS_DIR, 
    LOG_LEVEL, LOG_FORMAT, LOG_FILE,
    LOGO_FILE
)

# Setup logging before anything else
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)

# FastAPI App Initialization (only once!)
app = FastAPI(
    title="Neural Document Acquisition System",
    description="Intelligentes System zum Sammeln und Analysieren von Dokumenten",
    version="2.0.0"
)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Logo path for dashboard
LOGO_PATH = "/static/images/logo.png"

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Wird beim Start der Anwendung ausgeführt"""
    logger.info("Starting Neural Document Acquisition System")
    logger.info(f"Static files path: {STATIC_DIR}")
    logger.info(f"Templates path: {TEMPLATES_DIR}")
    
    # Überprüfe wichtige Verzeichnisse
    directories = {
        "Static": STATIC_DIR,
        "Templates": TEMPLATES_DIR,
        "Logs": LOGS_DIR
    }
    
    for name, path in directories.items():
        if path.exists():
            logger.info(f"{name} directory found: {path}")
        else:
            logger.warning(f"{name} directory not found at: {path}")
            
    # Überprüfe Logo
    if LOGO_FILE.exists():
        logger.info(f"Logo found: {LOGO_FILE}")
    else:
        logger.warning(f"Logo file not found at: {LOGO_FILE}")

# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Neural Document Acquisition System")

# Import and register routes
print("Registering routes...")
try:
    from app.routes import router
    app.include_router(router)
    logger.info("API routes registered successfully")
except Exception as e:
    logger.error(f"Failed to register routes: {str(e)}")
    raise

# Import websockets!
print("Setting up websockets...")
try:
    from app.websockets import *
    logger.info("WebSockets setup complete")
except Exception as e:
    logger.error(f"Failed to setup websockets: {str(e)}")
    raise

# Global FastAPI App instance
app_instance = app

print("Initialization complete!")