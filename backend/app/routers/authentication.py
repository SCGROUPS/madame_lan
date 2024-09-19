from fastapi import APIRouter
from starlette.responses import Response

from app.config import LOGGER
from app.core.authentication import check_authentication
from app.utils.service_result import handle_result


router = APIRouter()


@router.post("/api/authentication/{access_token}")
def authentication(access_token: str) -> Response:
    LOGGER.info("Request:")
    response = check_authentication(access_token)
    LOGGER.info("Response: response={}".format(response.value))
    return handle_result(response)
