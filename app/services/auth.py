from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlmodel import select, Session

from app.core import SecurityUtils
from app.models import User, Token, TokenData, LoginForm
from app.exceptions.http import UnauthorizedException, NotFoundException

oauth = OAuth2PasswordBearer("/api/v1/auth/login")


class _AuthService:

    def authenticate(self, form: LoginForm, session: Session) -> Token:
        """"""
        statement = select(User).where(User.email == form.email, User.deleted_at.is_(None)) # type: ignore
        user: User | None = session.exec(statement).first()

        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        if not user.is_active():
            raise UnauthorizedException("This account has been deactivated. Please contact your admin.")
        
        if not SecurityUtils.check_password(form.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")
        
        return SecurityUtils.create_token(user.id, user.role)

def get_auth_service() -> _AuthService:
    """"""
    return _AuthService()


def get_current_user(token: str = Depends(oauth)) -> TokenData:
    """"""
    return SecurityUtils.decode_token(token, "access")


AuthService = Annotated[_AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[TokenData, Depends(get_current_user)]
