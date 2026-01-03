from fastapi import APIRouter

from app.models import Token, TokenData, LoginForm
from app.services import AuthService, CurrentUser
from app.database import Session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token, status_code=201)
def login(form: LoginForm, service: AuthService, session: Session) -> Token:
    """"""
    return service.authenticate(form, session)


@router.get("/me", response_model=TokenData, status_code=200)
def get_current_user(user: CurrentUser) -> TokenData:
    """"""
    return user
