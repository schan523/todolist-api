from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import aggregation
from google.cloud.firestore_v1.base_query import FieldFilter
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
    query = db.collection("users").where(filter=FieldFilter("email", "==", user.email)).limit(1)
    aggregate_query = aggregation.AggregationQuery(query)
    aggregate_query.count(alias="all")
    result = aggregate_query.get()[0][0].value

    if result:
        raise HTTPException(status_code=400, detail="A user has already been registered with this email address")
        
    else:
        db.collection("users").add({
            "name": user.name,
            "email": user.email,
            "password": user.password
        })
    
    return user