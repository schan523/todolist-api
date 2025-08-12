from dotenv import load_dotenv
import os 

import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_app = firebase_admin.initialize_app(cred)