from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app.models import Token, TokenData, LoginForm
from app.services import AuthService, CurrentUser
from app.database import Session
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token, status_code=201)
@limiter.limit("5/minute")
def login(
    request: Request,
    service: AuthService,
    session: Session,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    ) -> Token:
    """Authenticate user and return JWT access token. Rate limited to 5 requests per minute."""
    return service.authenticate(LoginForm(email=form.username, password=form.password), session)


@router.get("/me", response_model=TokenData, status_code=200)
def get_current_user(user: CurrentUser) -> TokenData:
    """"""
    return user
