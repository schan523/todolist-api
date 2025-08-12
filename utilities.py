from dotenv import load_dotenv
import os 

from fastapi import HTTPException, Depends
from typing import Annotated
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError

from firebase_config import firebase_app
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from datetime import datetime, timedelta, timezone
from pydantic import EmailStr


# functions for password hashing and verifying 
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
db = firestore.client()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)

def get_user(email: EmailStr):
    docs = list(db.collection("users").where(filter=FieldFilter("email", "==", email)).limit(1).stream())
    if not docs:
        return None
    return docs[0].to_dict()

def authenticate_user(email: EmailStr, password: str):
    user = get_user(email)
    if user is None:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credientials_exception = HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"}) 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise credientials_exception
    except InvalidTokenError:
        raise credientials_exception
    
    user = get_user(email)
    if user is None:
        raise credientials_exception
    return user