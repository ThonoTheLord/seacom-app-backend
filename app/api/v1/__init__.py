from fastapi import APIRouter
from .auth import router as auth_router
from .user import router as user_router
from .technician import router as technician_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(technician_router)
