from fastapi import FastAPI
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os 

load_dotenv()
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_app = firebase_admin.initialize_app(cred)
db = firestore.client()
app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/")
async def root():
    return {"message": "Hello World"}


# User Registration Endpoint
class User(BaseModel):
    name: str
    email: str
    password: str 

@app.post("/register")
async def create_user(user: User):
    db.collection("users").add({
        "name": user.name,
        "email": user.email,
        "password": user.password
    })
    return user