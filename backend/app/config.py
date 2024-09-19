import os
from pathlib import Path

from dotenv import load_dotenv

from .setup import TIMEZONE, TIME_STR
from .setup import PYTHON_PATH, APP_PATH, AUDIO_TMP_DIR
from .log.timeit import timeit, async_timeit
from .log.log import get_log, LOG_TYPE
from .core.utils import load_yaml

LOGGER = get_log(name=LOG_TYPE.LOCAL)


# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # config for database
    DB_CONECTION = os.getenv('DB_CONECTION')
    DB_TABLE_CLIENT = os.getenv('DB_TABLE_CLIENT')
    DB_TABLE_CONVERSATION = os.getenv('DB_TABLE_CONVERSATION')

    # config for speech
    SPEECH_REGION = os.getenv('SPEECH_REGION')
    SPEECH_KEY = os.getenv('SPEECH_KEY')
    SPEECH_PRIVATE_ENDPOINT = os.getenv('SPEECH_PRIVATE_ENDPOINT')

    # config for ChatGPT
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
    AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv('AZURE_OPENAI_EMB_DEPLOYMENT')

    # for search option
    SEACHER_PATH = os.path.join(APP_PATH, 'conf', 'searcher.yaml')
    SEACHER = load_yaml(SEACHER_PATH)
    LOCAL_SEARCH = SEACHER.get("local_search", 3)
    INTERNET_SEARCH = int(SEACHER.get("internet_search", 3))
    SEARCH_WITH_EMOTION = bool(SEACHER.get("search_with_emotion", False))
    HISTORY_LENGTH = int(SEACHER.get("history_length", 2))
    STATUS_DURATION = int(SEACHER.get("status_duration", 3600))
    OUTDATE_DURATION = int(SEACHER.get("outdate_duration", 3600))


    # config for Azure search
    COGNITIVE_SEARCH_ENDPOINT = os.getenv('COGNITIVE_SEARCH_ENDPOINT')
    COGNITIVE_SEARCH_API_KEY = os.getenv('COGNITIVE_SEARCH_API_KEY')
    COGNITIVE_SEARCH_INDEX_NAME = os.getenv('COGNITIVE_SEARCH_INDEX_NAME')
    # config for Bing search
    BING_SUBSCRIPTION_KEY = os.getenv('BING_SUBSCRIPTION_KEY')
    BING_SEARCH_URL = os.getenv('BING_SEARCH_URL')

    ICE_SERVER_URL = os.getenv('ICE_SERVER_URL')
    ICE_SERVER_URL_REMOTE = os.getenv('ICE_SERVER_URL_REMOTE')
    ICE_SERVER_USERNAME = os.getenv('ICE_SERVER_USERNAME')
    ICE_SERVER_PASSWORD = os.getenv('ICE_SERVER_PASSWORD')

    # config for languages
    TTS_VOICE = os.getenv('TTS_VOICE')
    STT_LOCALES = os.getenv('STT_LOCALES')
    LANGUAGE_DEFAULT = "vi-VN"
    LANGUAGES_PATH = os.path.join(APP_PATH, 'conf', 'languages.yaml')
    LANGUAGES = load_yaml(LANGUAGES_PATH)

    # config for logo
    LOGO_PATH = os.path.join(APP_PATH, "conf", "logo.yaml")
    LOGO = load_yaml(LOGO_PATH).get(COGNITIVE_SEARCH_INDEX_NAME, load_yaml(LOGO_PATH)['default'])

    # config for prompt
    SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT')
    PROMPT_PATH = os.path.join(APP_PATH, "conf", "prompt.yaml")
    PERSONA = load_yaml(PROMPT_PATH).get(COGNITIVE_SEARCH_INDEX_NAME, "default")

    # config for title
    TITLE_DEFAULT = "Tôi là trợ lý ảo."
    TITLE_PATH = os.path.join(APP_PATH, "conf", "titles.yaml")
    TITLES = load_yaml(TITLE_PATH).get(COGNITIVE_SEARCH_INDEX_NAME, "default")
    for k in LANGUAGES.keys():
        LANGUAGES[k]['title'] = TITLES[k] if k in TITLES else TITLE_DEFAULT

    # config for greeting
    GREETING_DEFAULT = "Xin chào!"
    GREETING_PATH = os.path.join(APP_PATH, "conf", "greeting.yaml")
    GREETING = load_yaml(GREETING_PATH).get("default", "")
    for k in LANGUAGES.keys():
        LANGUAGES[k]['greeting'] = GREETING[k] if k in GREETING else GREETING_DEFAULT

    # config for chat excption
    CHAT_EXCEPTION_DEFAULT = "Xin lỗi, tôi không thể trả lời câu hỏi này. Vui lòng hỏi câu hỏi khác!"
    CHAT_EXCEPTION_PATH = os.path.join(APP_PATH, "conf", "exceptions.yaml")
    CHAT_EXCEPTION = load_yaml(CHAT_EXCEPTION_PATH).get("default", "")

    # config for waiting response
    WAITING_DEFAULT = {
        "001":{
            "text": "Vui lòng chờ tôi chút xíu nhé, tôi sẽ kiểm tra lại thông tin.",
            "audio_path": "/static/audio/waiting/vi-VN/001.wav"
            }
        }
    WAITING_PATH = os.path.join(APP_PATH, "conf", "waiting.yaml")
    WAITINGS = load_yaml(WAITING_PATH)
    WAITINGS = WAITINGS.get("default", "")
    for k in LANGUAGES.keys():
        LANGUAGES[k]['waiting'] = WAITINGS[k] if k in WAITINGS else WAITING_DEFAULT

def show_config():
    attrs = (name for name in vars(Config) if not name.startswith('_'))
    for attr in attrs:
        LOGGER.info("-{}={}".format(attr, getattr(Config, attr)))
