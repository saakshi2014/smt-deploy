import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
import os


load_dotenv()
_firebase_app = None


def initialize_firebase():
    """
    Initialises Firebase Admin SDK.
    Supports both local (JSON file) and cloud (environment variable) modes.
    """
    global _firebase_app

    if _firebase_app:
        return _firebase_app

    import os
    import json

    try:
        # ── Cloud deployment: read from environment variable ───────────────────
        service_account_json = os.environ.get(
            'FIREBASE_SERVICE_ACCOUNT_JSON')

        if service_account_json:
            print("Initialising Firebase from environment variable...")
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)

        else:
            # ── Local development: read from JSON file ─────────────────────────
            service_account_path = os.environ.get(
                'GOOGLE_APPLICATION_CREDENTIALS',
                'firebase-service-account.json'
            )

            # Try project root first
            if not os.path.isabs(service_account_path):
                project_root = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
                service_account_path = os.path.join(
                    project_root, service_account_path
                )

            print(f"Looking for service account at: {service_account_path}")
            cred = credentials.Certificate(service_account_path)

        _firebase_app = firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialised successfully")
        return _firebase_app

    except Exception as e:
        print(f"Firebase initialisation error: {e}")
        raise

def get_firestore_client():
    initialize_firebase()
    return firestore.client()