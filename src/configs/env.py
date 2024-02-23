import json
import os

from dotenv import load_dotenv

# Env variables
load_dotenv()

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT")
IS_DEV_ENVIRONMENT = ENVIRONMENT == "development"

# Firebase
CERTIFICATE_CONTENT = json.loads(os.getenv("FIREBASE_CERTIFICATE_CONTENT"))
BUCKET_NAME = os.getenv("BUCKET_NAME")
UPDATE_PROJECT_URL = os.getenv("UPDATE_PROJECT_URL")

# Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN")

# Microsoft Translator
MICROSOFT_TRANSLATOR_API_KEY = os.getenv("MICROSOFT_TRANSLATOR_API_KEY")
MICROSOFT_TRANSLATOR_REGION = os.getenv("MICROSOFT_TRANSLATOR_REGION")
