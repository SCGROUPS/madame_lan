from fastapi import APIRouter
from starlette.responses import Response

from app.config import LOGGER
from app.core.authentication import check_authentication
from app.utils.app_exceptions import AppExceptionCase
from app.utils.service_result import ServiceResult
from app.utils.service_result import handle_result
from app.db.api import DB


router = APIRouter()

def create_client(access_token: str) -> ServiceResult:
    try:
        data = {}
        client_id = DB.create(access_token)
        data = {'client_id': str(client_id)}
    except Exception as e:
        LOGGER.error("Exception: {}".format(e))
        return ServiceResult(AppExceptionCase(status_code=400, context=str(e)))
    return ServiceResult(data)

def update_client(access_token: str, client_id: str) -> ServiceResult:
    try:
        data = {}
        client_id = DB.update(access_token, client_id)
        data = {'client_id': str(client_id)}
    except Exception as e:
        LOGGER.error("Exception: {}".format(e))
        return ServiceResult(AppExceptionCase(status_code=400, context=str(e)))
    return ServiceResult(data)

@router.get("/api/getClientId/{access_token}")
async def getClientId(access_token: str) -> Response:
    LOGGER.info("Request:")
    authen = check_authentication(access_token)
    if not check_authentication(access_token).success:
        return handle_result(authen)

    response = create_client(access_token)
    LOGGER.info("Response: response={}".format(response.value))
    return handle_result(response)

@router.put("/api/getClientId/{access_token}")
async def getClientId(access_token: str, client_id: str) -> Response:
    LOGGER.info("Request:")
    authen = check_authentication(access_token)
    if not check_authentication(access_token).success:
        return handle_result(authen)

    response = update_client(access_token, client_id)
    LOGGER.info("Response: response={}".format(response.value))
    return handle_result(response)
