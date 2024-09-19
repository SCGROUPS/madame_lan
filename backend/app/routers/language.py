from operator import itemgetter

from fastapi import APIRouter
from starlette.responses import Response

from app.config import Config, LOGGER
from app.core.authentication import check_authentication
from app.utils.app_exceptions import AppExceptionCase
from app.utils.service_result import ServiceResult
from app.utils.service_result import handle_result

router = APIRouter()


def get_languages() -> ServiceResult:
    try:
        data = []
        language_list = Config.STT_LOCALES.split(',')
        language_list = sorted(language_list, key=itemgetter(3), reverse=False)
        language_default = Config.LANGUAGE_DEFAULT if Config.LANGUAGE_DEFAULT in language_list else language_list[0]

        for code in language_list:
            default = False
            if code in Config.LANGUAGES:
                default = True if code == language_default else False
                details = Config.LANGUAGES[code]
                item = {"country": details["country"],
                        "greeting": details["greeting"],
                        "title": details["title"],
                        "version": details["version"],
                        "waiting": details["waiting"],
                        "welcome": details["welcome"],
                        "introduce": details["introduce"],
                        "assistant": details["assistant"],
                        "delete_history": details["delete_history"],
                        "clear_history": details["clear_history"],
                        "days_of_week": details["days_of_week"],
                        "language_code": code,
                        "default": default,
                        "image_path": f"/static/image/flag/{details['image_file']}",
                        "voice_name": details["voice_name"]
                        }
                data.append(item)
    except Exception as e:
        LOGGER.error("Exception: {}".format(e))
        return ServiceResult(AppExceptionCase(status_code=400, context=str(e)))
    return ServiceResult(data)

def get_logo() -> ServiceResult:
    try:
        data = {}
        data['logo'] = Config.LOGO
    except Exception as e:
        LOGGER.error("Exception: {}".format(e))
        return ServiceResult(AppExceptionCase(status_code=400, context=str(e)))
    return ServiceResult(data)

# The API route to get language list
@router.get("/api/getLanguageList/{access_token}")
async def get_language_list(access_token: str) -> Response:
    LOGGER.info("Request:")
    authen = check_authentication(access_token)
    if not check_authentication(access_token).success:
        return handle_result(authen)

    response = get_languages()
    LOGGER.info("Response: response={}".format(response.value))
    return handle_result(response)

# The API route to get logo images
@router.get("/api/getLogoImages/{access_token}")
async def get_logo_images(access_token: str) -> Response:
    LOGGER.info("Request:")
    authen = check_authentication(access_token)
    if not check_authentication(access_token).success:
        return handle_result(authen)

    response = get_logo()
    LOGGER.info("Response: response={}".format(response.value))
    return handle_result(response)
