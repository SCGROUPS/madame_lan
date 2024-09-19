import uuid
import pytz
import json
from datetime import datetime

from app.config import TIMEZONE, TIME_STR

def uuid2str(id: uuid.UUID):
    return f'{id}'

def get_datetime_now() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))

def time2str(dt):
    if isinstance(dt, str):
        return dt
    return dt.strftime(TIME_STR)[:-3]

def get_tz():
    return pytz.timezone(TIMEZONE)

def to_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_json(path):
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data
