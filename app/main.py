from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.database import Database
from app.core import app_settings
from app.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.connect(app_settings.database_url)
    Database.init()
    yield
    Database.disconnect()


app: FastAPI = FastAPI(
    title="Seacom-App",
    version="0.1.0",
    description="",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/", include_in_schema=False, status_code=307)
def root() -> RedirectResponse:
    """"""
    return RedirectResponse(app.docs_url or "/docs")
