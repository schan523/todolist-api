from pydantic import BaseModel, EmailStr


class User(BaseModel):
    name: str
    email: EmailStr
    password: str 

class Login(BaseModel):
    email: EmailStr
    password: str

class ToDo(BaseModel):
    title: str
    description: str