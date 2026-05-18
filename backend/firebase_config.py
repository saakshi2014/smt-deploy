import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
import os

load_dotenv()


def initialize_firebase():
    if not firebase_admin._apps:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        service_account_path = os.path.join(project_root, "firebase-service-account.json")
        print(f"Looking for service account at: {service_account_path}")
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"File not found: {service_account_path}")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            "projectId": os.getenv("FIREBASE_PROJECT_ID")
        })
        print("Firebase Admin SDK initialised successfully")
    return firebase_admin.get_app()


def get_firestore_client():
    initialize_firebase()
    return firestore.client()


def get_auth_client():
    initialize_firebase()
    return auth