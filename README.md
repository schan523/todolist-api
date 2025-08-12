# Todo List API

Fast API was used for this implementation.

## Setup
To start, create a virtual environment using venv:
```
python -m venv .venv
```
To activate, run the following command in your terminal, in the base project directory:
```
.venv/Scripts/Activate.ps1
```
To deactivate:
```
deactivate
```
Install dependencies:
```
pip install -r requirements.txt
```
Next, create a new Firebase project at https://console.firebase.google.com/, and create a Cloud Firestore database. Generate a new private key in "Service Accounts" of the project settings, pasting the content into a new file named "service-account.json". Create a .env file to create a key for the path to the service-account.json and remember to add .env and service-account.json to .gitignore.

To run the app, run:
```
fastapi dev main.py
```
