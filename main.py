from dotenv import load_dotenv
import os 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
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

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# functions for password hashing and verifying 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=ALGORITHM)
    return encoded_jwt


@app.get("/")
async def root():
    return {"message": "Hello World"}


# User Registration Endpoint
@app.post("/register")
async def create_user(user: User):
    query = db.collection("users").where(filter=FieldFilter("email", "==", user.email)).limit(1)
    aggregate_query = aggregation.AggregationQuery(query)
    aggregate_query.count(alias="all")
    result = aggregate_query.get()[0][0].value

    if result:
        raise HTTPException(status_code=400, detail="A user has already been registered with this email address")
        
    else:
        data = {
            "name": user.name,
            "email": user.email,
            "password": get_password_hash(user.password)
        }
        db.collection("users").add(user.to_dict())
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {"token": create_access_token(data, access_token_expires)}


# User Login
@app.post("/login") 
async def login(login_details : Login):
    email = login_details.email
    password = login_details.password

    docs = db.collection("users").where(filter=FieldFilter("email", "==", email)).stream()
    for doc in docs:
        user = doc.to_dict()
    
    if verify_password(password, user["password"]):
        return {"token": create_access_token({"email": email, "password": password}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))}
    else:
        raise HTTPException(status_code=400, detail="Password does not match")
