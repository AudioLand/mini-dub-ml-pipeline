from firebase_admin import credentials, initialize_app, firestore

from configs.env import CERTIFICATE_CONTENT


def init_firebase():
    cred = credentials.Certificate(CERTIFICATE_CONTENT)
    initialize_app(cred)


def get_firestore():
    return firestore.client()
