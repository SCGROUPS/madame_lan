import os
import logging
import logging.handlers as handlers

from ..setup import LOG_DIR, LOG_FILE
from ..core.utils import get_map_from_file


class LOG_TYPE:
    LOCAL = 'local'
    MIDDLEWARE = 'middleware'
    TIMEIT = 'timeit'


class LOG_LEVEL:
    NOTSET = 'NOTSET'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL' 


def get_log(name=LOG_TYPE.LOCAL):
    config = LOG_FILE.format(name)
    log = logging.getLogger(name)
    settingmaps = get_map_from_file(config)

    logTemplate = settingmaps["template"]
    logFormatter = logging.Formatter(logTemplate)

    outFile = settingmaps["outfile"].strip()
    outPath = os.path.join(LOG_DIR, outFile)

    fileHandler = logging.FileHandler(outPath, encoding="utf-8")
    fileHandler = handlers.TimedRotatingFileHandler(outPath, when="midnight", interval=1, encoding="utf-8")
    fileHandler.suffix = "%Y%m%d.log"
    fileHandler.terminator = ""
    fileHandler.setFormatter(logFormatter)

    level = settingmaps["level"].strip()

    if level == LOG_LEVEL.NOTSET:
        log.setLevel(logging.NOTSET)
    elif level == LOG_LEVEL.DEBUG:
        log.setLevel(logging.DEBUG)
    elif level == LOG_LEVEL.INFO:
        log.setLevel(logging.INFO)
    elif level == LOG_LEVEL.WARNING:
        log.setLevel(logging.WARNING)
    elif level == LOG_LEVEL.ERROR:
        log.setLevel(logging.ERROR)
    elif level == LOG_LEVEL.CRITICAL:
        log.setLevel(logging.CRITICAL)
    else:
        log.setLevel(logging.INFO)
    log.addHandler(fileHandler)

    to_console = settingmaps["console"].strip()
    if str(to_console).upper() == str(True).upper():
        consoleHandler = logging.StreamHandler()
        consoleHandler.terminator = ""
        consoleHandler.setFormatter(logFormatter)
        log.addHandler(consoleHandler)

    return log