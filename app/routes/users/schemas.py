from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str
    image: str

    class Config:
        form_attributes = True

class User(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserValidate(BaseModel):
    email: str
    password: str

    class Config:
        form_attributes = True