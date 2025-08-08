from dotenv import load_dotenv
import os 

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Annotated
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import aggregation
from google.cloud.firestore_v1.base_query import FieldFilter
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError

load_dotenv()
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()
app = FastAPI()


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

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# functions for password hashing and verifying 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)

def get_user(email: EmailStr):
    return db.collection("users").where(filter=FieldFilter("email", "==", email)).limit(1)

def authenticate_user(email: EmailStr, password: str):
    user = get_user(email).to_dict()
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
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credientials_exception = HTTPException(status_code=401, detail="Unauthorized") 
    try:
        payload = jwt.decode(token, os.getenv("SECRET_CODE"), algorithm=ALGORITHM)
        email = payload.get("email")
        if email is None:
            raise credientials_exception
    except InvalidTokenError:
        raise credientials_exception
    
    query = db.collection("users").where(filter=FieldFilter("email", "==", email))
    return {"email": email}

# User Registration Endpoint
@app.post("/register")
async def create_user(user: User):
    query = get_user(user.email)
    aggregate_query = aggregation.AggregationQuery(query)
    aggregate_query.count(alias="all")
    result = aggregate_query.get()[0][0].value

    if result:
        raise HTTPException(status_code=400, detail="A user has already been registered with this email address")
        
    else:
        user_dict = user.model_dump().copy()
        user_dict["password"] = get_password_hash(user.password)
        db.collection("users").add(user_dict)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {"token": create_access_token(user.model_dump, access_token_expires)}


# User Login
@app.post("/login") 
async def login(login_details : Login):
    email = login_details.email
    password = login_details.password

    user = authenticate_user(email, password)

    docs = db.collection("users").where(filter=FieldFilter("email", "==", email)).stream()
    for doc in docs:
        user = doc.to_dict()
    
    if verify_password(password, user["password"]):
        return {"token": create_access_token({"email": email, "password": password}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))}
    else:
        raise HTTPException(status_code=400, detail="Password does not match")


@app.post("/todos")
async def create_to_do(to_do: ToDo):

    return {}

