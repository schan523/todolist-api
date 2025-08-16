from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
import random

from utilities import get_current_user
from models import ToDo

from firebase_admin import firestore
from firebase_config import firebase_app
from google.cloud.firestore_v1.base_query import FieldFilter


db = firestore.client()
router = APIRouter(
    tags=["todos"]
)


@router.post("/todos")
async def create_to_do(to_do: ToDo, current_user : Annotated[dict, Depends(get_current_user)]):
    to_do_dict = to_do.model_dump()
    title = to_do_dict["title"]
    desc = to_do_dict["description"]
    to_do_dict["user_id"] = current_user["user_id"]
    id = random.randint(1, 10**6)
    while True:
        if not any(db.collection("tasks").where(filter=FieldFilter("id", "==", id)).stream()):
            break
        else:
            id = random.randint(1, 10**6)

    to_do_dict["id"] = id
    db.collection("tasks").add(to_do_dict)
    return {"id": to_do_dict["id"], "title": title, "description": desc}


@router.put("/todos/{id}")
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


@router.delete("/todos/{id}", status_code=204)
async def delete_todo(id : int, current_user : Annotated[dict, Depends(get_current_user)]):
    query = db.collection("tasks").where(filter=FieldFilter("id", "==", id)).stream()
    doc = list(query)[0]
    data = doc.to_dict()
    if data["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden: the current user is not the creator of the to-do item.")
    
    db.collection("tasks").document(doc.id).delete()
    return 


@router.get("/todos")
async def get_todo(current_user : Annotated[dict, Depends(get_current_user)], page : int = 1, limit: int = 10):
    user_id = current_user["user_id"]
    data = []
    query = db.collection("tasks").where(filter=FieldFilter("user_id", "==", user_id)).order_by("id")
    num_results = len(list(query.stream()))
    if (page-1)*limit >= num_results:
        raise HTTPException(status_code=400, detail="There are not enough results.")
    
    curr_page_cutoff = list(query.stream())[(page-1)*limit]
    cutoff_id = curr_page_cutoff.to_dict()["id"]
    page_query = query.start_at({"id": cutoff_id}).stream()
    for doc in page_query:
        doc_data = doc.to_dict()
        data.append({
            "id": doc_data["id"],
            "title": doc_data["title"],
            "description": doc_data["description"]
        })
    return {"data": data, "page": page, "limit": limit, "total": num_results}