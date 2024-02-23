import os

# Get the absolute path to the directory where the current script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path to the project directory by going up one level
project_dir = os.path.dirname(current_dir)

PROCESSING_FILES_DIR_PATH = f"{project_dir}/tmp"

VIDEO_SUPPORTED_EXTENSIONS = ["mp4", "avi"]
AUDIO_SUPPORTED_EXTENSIONS = ["mp3"]
