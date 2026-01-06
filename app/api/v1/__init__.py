from fastapi import APIRouter
from .auth import router as auth_router
from .user import router as user_router
from .technician import router as technician_router
from .site import router as site_router
from .task import router as task_router
from .incident import router as incident_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(technician_router)
router.include_router(site_router)
router.include_router(task_router)
router.include_router(incident_router)
