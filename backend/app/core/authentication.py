import os

from app.config import APP_PATH, LOGGER, load_yaml
from app.utils.app_exceptions import AppException
from app.utils.service_result import ServiceResult

# config for access token
TOKEN_PATH = os.path.join(APP_PATH, "conf", "access_tokens.yaml")
TOKENS = load_yaml(TOKEN_PATH).get("default", "")


def is_valid_token(access_token: str):
    return True if access_token in TOKENS.values() else False

def check_authentication(access_token: str) -> ServiceResult:
    if not is_valid_token(access_token):
        return ServiceResult(AppException.AccessTokenNotFound({"access_token": access_token}))
    LOGGER.info("Authentication: name={}".format([k for k, v in TOKENS.items() if v==access_token]))
    data = {"access_token": access_token}
    return ServiceResult(data) 
