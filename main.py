from dotenv import load_dotenv
import os 

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
import uuid
import random

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
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

# functions for password hashing and verifying 
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

# User Registration Endpoint
@app.post("/register")
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
@app.post("/login") 
async def login(form_data : Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if user:
        return {"access_token": create_access_token({"email": user["email"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)), "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Invalid login details")


@app.get("/me")
async def debug(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user


@app.post("/todos")
async def create_to_do(to_do: ToDo, current_user : Annotated[dict, Depends(get_current_user)]):
    to_do_dict = to_do.model_dump()
    title = to_do_dict["title"]
    desc = to_do_dict["description"]
    to_do_dict["user_id"] = current_user["user_id"]
    to_do_dict["id"] = random.randint(1, 1000)
    db.collection("tasks").add(to_do_dict)
    return {"id": to_do_dict["id"], "title": title, "description": desc}


@app.post("/todos/{id}")
async def update_to_do(id: int, to_do : ToDo, current_user : Annotated[dict, Depends(get_current_user)]):
    docs = db.collection("tasks").where(filter=FieldFilter("id", "==", id)).limit(1).stream()
    doc = list(docs)[0]
    data = doc.to_dict()
    if data["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden: the current user is not the creator of the to-do item.")
    
    document = db.collection("tasks").document(doc.id)
    document.update({"title": to_do.title})
    document.update({"description": to_do.description})
    results = document.get().to_dict()
    return {"id": id, "title": to_do.title, "description": to_do.description}

