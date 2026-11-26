import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import init_db, get_db
from backend.api.routes import router as api_router
from backend.observability import get_prometheus_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tracemind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s v%s...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Database URL: %s", settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL)
    logger.info("LLM Integration: %s (Model: %s)", "ENABLED" if settings.ENABLE_LLM else "FALLBACK (Deterministic Rules)", settings.GROQ_MODEL)
    
    # Initialize DB tables
    try:
        init_db()
    except Exception as e:
        logger.error("Error during database initialization: %s", str(e))
        
    yield
    
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Root-Cause Analysis and Self-Healing System for Distributed Applications",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for cleaner errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception at %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify telemetry signals."}
    )

# Include API Router
app.include_router(api_router)


@app.get("/metrics")
def prometheus_metrics(db: Session = Depends(get_db)):
    return Response(
        content=get_prometheus_metrics(db),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.py:app", host="0.0.0.0", port=8000, reload=True)
