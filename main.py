from fastapi import FastAPI, Depends
from routers import users, todos
from typing import Annotated

from utilities import get_current_user

app = FastAPI()

app.include_router(users.router)
app.include_router(todos.router)


@app.get("/me")
async def debug(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user

