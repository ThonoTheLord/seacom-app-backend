from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app.models import Token, TokenData, LoginForm
from app.services import AuthService, CurrentUser
from app.database import Session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token, status_code=201)
def login(
    service: AuthService,
    session: Session,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    ) -> Token:
    """"""
    return service.authenticate(LoginForm(email=form.username, password=form.password), session)


@router.get("/me", response_model=TokenData, status_code=200)
def get_current_user(user: CurrentUser) -> TokenData:
    """"""
    return user
