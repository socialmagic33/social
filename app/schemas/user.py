from pydantic import BaseModel, EmailStr, validator
import re

class PasswordValidator:
    @staticmethod
    def validate(password: str) -> bool:
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False
        return True

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator("password")
    def validate_password(cls, v):
        if not PasswordValidator.validate(v):
            raise ValueError(
                "Password must be at least 8 characters long and contain "
                "uppercase, lowercase, number, and special character"
            )
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool

    class Config:
        orm_mode = True

class UserSetup(BaseModel):
    company_name: str
    values: str
    specialties: str