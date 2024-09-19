import os
from pathlib import Path


PYTHON_PATH = str(Path(__file__).resolve().parent.parent)
APP_PATH = os.path.join(PYTHON_PATH, "app")
STORAGE_DIR = os.path.join(os.path.dirname(PYTHON_PATH), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


# Set timezone
TIMEZONE = 'Asia/Bangkok' #UTC #Asia/Bangkok #Asia/Tokyo
TIME_STR = "%Y-%m-%d %H:%M:%S.%f" #[:-3]

# Set logging
LOG_DIR = os.path.join(STORAGE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(APP_PATH, "conf", "log", "{}.conf")

# Set audio tmp dir
AUDIO_TMP_DIR = os.path.join(APP_PATH, "static", "audio", "tmp")
os.makedirs(os.path.dirname(AUDIO_TMP_DIR), exist_ok=True)
os.makedirs(AUDIO_TMP_DIR, exist_ok=True)
