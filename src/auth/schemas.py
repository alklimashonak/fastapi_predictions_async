from pydantic import BaseModel, EmailStr, UUID4


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str | None = None


class UserBase(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class UserRead(UserBase):
    id: UUID4 | None = None

    class Config:
        orm_mode = True


class UserDB(UserRead):
    hashed_password: str
