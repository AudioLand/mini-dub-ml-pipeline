from firebase_admin import storage

from configs.env import BUCKET_NAME

bucket = storage.bucket(name=BUCKET_NAME)
MINI_PROJECTS_COLLECTION = "mini-projects"
