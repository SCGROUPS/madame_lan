import os
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi_utils.tasks import repeat_every
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.config import APP_PATH, LOGGER, show_config, AUDIO_TMP_DIR, Config
from app.routers import authentication as authen
from app.routers import client, language, chat
from app.db.api import DB
from app.log.middleware import LogMiddleware
from app.utils.app_exceptions import app_exception_handler, AppExceptionCase
from app.utils.request_exceptions import http_exception_handler, request_validation_exception_handler


app = FastAPI()
LOGGER.info("\n\n\nStart AI Assistant webapp!\n")
LOGGER.info("Config:")
LOGGER.info("{}".format(show_config()))

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Set statics
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/assets", StaticFiles(directory="app/static/reactjs/assets/"), name="assets")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, e):
    return await http_exception_handler(request, e)

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request, e):
    return await request_validation_exception_handler(request, e)

@app.exception_handler(AppExceptionCase)
async def custom_app_exception_handler(request, e):
    return await app_exception_handler(request, e)

@app.on_event("startup")
@repeat_every(seconds=60)
def cleanup_audio_files() -> None:
    LOGGER.info("Start:")
    now = datetime.now()
    for filename in os.listdir(AUDIO_TMP_DIR):
        file_path = os.path.join(AUDIO_TMP_DIR, filename)
        if os.path.isfile(file_path) and filename.endswith('.wav'):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if now - file_creation_time > timedelta(minutes=20):
                os.remove(file_path)
                LOGGER.info(f"Deleted old audio file: {filename}")
    LOGGER.info("Done!")

@app.on_event("startup")
@repeat_every(seconds=Config.STATUS_DURATION)
def update_client_status() -> None:
    LOGGER.info("Start:")
    DB.update_status()
    LOGGER.info("Done!")

@app.on_event("startup")
@repeat_every(seconds=Config.OUTDATE_DURATION)
def save_to_database() -> None:
    LOGGER.info("Start:")
    DB.save_inactive_clients()
    DB.save_active_clients()
    LOGGER.info("Done!")

# The default route, which shows the default web page
@app.get("/")
@app.get("/authentication")
async def read_index():
    return FileResponse(os.path.join(APP_PATH, "static", "reactjs", "index.html"))

# Add middleware
app.add_middleware(LogMiddleware)

# Include authen
app.include_router(authen.router)

# Include routers
app.include_router(client.router)
app.include_router(language.router)
app.include_router(chat.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host='localhost', port=5001, reload=True)
