import time
import traceback

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware


from .log import get_log, LOG_TYPE


LOGGER = get_log(name=LOG_TYPE.MIDDLEWARE)


class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = None
            LOGGER.info("Request:")
            LOGGER.info("request.method: {}".format(request.method))
            LOGGER.info("request.url: {}".format(request.url))
            LOGGER.info("request.headers: {}".format(request.headers))
            LOGGER.info("request.headers.clientid: {}".format(request.headers.get("clientid", "")))
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(f'{process_time:0.4f} sec')
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                LOGGER.error("Exception: {}".format(response))
            LOGGER.info("Response:")
            LOGGER.info("response.status_code: {}".format(response.status_code))
            LOGGER.info("X-Process-Time: {}\n".format(response.headers.get("X-Process-Time", "")))
        except Exception as e:
            exc_traceback = traceback.format_exc()
            LOGGER.error("Exception: {}".format(e))
            LOGGER.error("Traceback: {}".format(exc_traceback))
        return response
