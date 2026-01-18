from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
import asyncio

from app.database import Database
from app.core import app_settings
from app.core.rate_limiter import limiter
from app.api import router


# Background task for SLA checking
async def sla_check_background_task():
    """Background task that periodically checks for SLA breaches."""
    from loguru import logger as LOG
    
    # Wait for startup to complete
    await asyncio.sleep(30)
    
    while True:
        try:
            from sqlmodel import Session
            from app.services.sla_checker import check_sla_breaches
            
            with Session(Database.connection) as session:
                warnings, breaches = check_sla_breaches(session)
                
                if warnings or breaches:
                    LOG.info(f"SLA Check: {len(warnings)} warnings, {len(breaches)} breaches found")
        except Exception as e:
            LOG.error(f"SLA check error: {e}")
        
        # Check every 15 minutes
        await asyncio.sleep(15 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.connect(app_settings.database_url)
    Database.init()
    
    # Start SLA check background task
    sla_task = asyncio.create_task(sla_check_background_task())
    
    yield
    
    # Cancel background task on shutdown
    sla_task.cancel()
    try:
        await sla_task
    except asyncio.CancelledError:
        pass
    
    Database.disconnect()


app: FastAPI = FastAPI(
    title="Seacom-App",
    version="0.1.0",
    description="Backend API for Seacom field technician management system",
    lifespan=lifespan
)

# Add state for limiter
app.state.limiter = limiter

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/", include_in_schema=False, status_code=307)
def root() -> RedirectResponse:
    """"""
    return RedirectResponse(app.docs_url or "/docs")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from loguru import logger as LOG
    LOG.debug("Validation error: {}", exc.errors())
    LOG.debug("Request body: {}", exc.body)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
