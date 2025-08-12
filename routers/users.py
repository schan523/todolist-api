from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import uuid
from typing import Annotated


import firebase_admin
from firebase_admin import firestore
from firebase_config import firebase_app
from google.cloud.firestore_v1.base_query import FieldFilter

from utilities import get_password_hash, authenticate_user, create_access_token
from models import User

router = APIRouter()
db = firestore.client()
ACCESS_TOKEN_EXPIRE_MINUTES = 30



# User Registration Endpoint
@router.post("/register", tags=["users"])
async def create_user(user: User):
    docs = db.collection("users").where(filter=FieldFilter("email", "==", user.email)).stream()
    if any(docs):
        raise HTTPException(status_code=400, detail="A user has already been registered with this email address")
    else:
        user_dict = user.model_dump()
        user_dict["password"] = get_password_hash(user.password)
        user_dict["user_id"] = str(uuid.uuid1())
        db.collection("users").add(user_dict)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {"access_token": create_access_token({"email": user_dict["email"]}, access_token_expires), "token_type": "bearer"}


# User Login
@router.post("/login", tags=["users"]) 
async def login(form_data : Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if user:
        return {"access_token": create_access_token({"email": user["email"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)), "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Invalid login details")