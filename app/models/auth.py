from pydantic import BaseModel, Field
from uuid import uuid4, UUID

from app.utils.enums import UserRole


class Token(BaseModel):
    """"""

    access_token: str = Field(
        description="JWT access token",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.dyt0CoTl4WoVjAHI9Q_CwSKhl6d_9rhM3NrXuJttkao"
        ],
    )
    token_type: str = Field(default="bearer", description="type of token")
    is_refresh: bool = Field(
        default=False, description="whether the access token is a refresh token or not"
    )


class TokenData(BaseModel):
    """"""

    user_id: UUID = Field(description="the current user's id", examples=[str(uuid4())])
    exp: int = Field(
        description="expiration time of the token in unix timestamp format", examples=[1700000000]
    )
    role: UserRole = Field(description="the current user's role")
