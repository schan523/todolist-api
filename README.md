# Todo List API

Fast API was used for this implementation.
Project link: https://roadmap.sh/projects/todo-list-api

## Setup
1. To start, create a virtual environment using venv:
```
python -m venv .venv
```
2. To activate, run the following command in your terminal, in the base project directory:
```
.venv/Scripts/Activate.ps1
```
To deactivate:
```
deactivate
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Next, create a new Firebase project at https://console.firebase.google.com/, and create a Cloud Firestore database. Generate a new private key in "Service Accounts" of the project settings, pasting the content into a new file named "service-account.json". Create a .env file to create a key for the path to the service-account.json and remember to add .env and service-account.json to .gitignore.

5. To run the app, run:
```
fastapi dev main.py
```
While the server is running, follow the link and add "/docs" to the end of the url to make use of FastAPI's SwaggerUI

## Endpoints
- FastAPI's APIRouter class is used to split the endpoints into the tags "users" (register, login) and "todos" (create, update, delete, and get To-Dos).
- In order to authenticate login tokens for the to-do endpoints, use the SwaggerUI "Authorize" button rather than the /login enpoint so the authentication token can be passed along.
- In order to use the get to-do endpoint, the first attempt may return an error in the terminal asking you to create a compound index in the Firebase database. Follow the link and do so, listing the fields "user_id" first and then "id".

