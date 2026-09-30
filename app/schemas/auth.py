from pydantic import BaseModel, ConfigDict, Field


class GoogleCredential(BaseModel):
    credential: str = Field(..., min_length=1, max_length=16384)


class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
