from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Credentials used to request an access token."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Access token payload returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
