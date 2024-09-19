import os
import time
import functools
from datetime import datetime

from app.log.log import get_log, LOG_TYPE

LOGGER = get_log(name=LOG_TYPE.TIMEIT)


def timeit():
    def decorator(func):
        @functools.wraps(func)
        def timeit(*args, **kwargs):
            ts = time.perf_counter()
            result = func(*args, **kwargs)
            te = time.perf_counter()
            LOGGER.debug("[{} - {}()] took {:.4f} sec.".format(os.path.basename(func.__code__.co_filename),
                                                     func.__qualname__, te-ts))
            return result
        return timeit
    return decorator

def async_timeit():
    def decorator(func):
        @functools.wraps(func)
        async def timeit(*args, **kwargs):
            ts = time.perf_counter()
            result = await func(*args, **kwargs)
            te = time.perf_counter()
            LOGGER.debug("[{} - {}()] took {:.4f} sec.".format(os.path.basename(func.__code__.co_filename),
                                                     func.__qualname__, te-ts))
            return result
        return timeit
    return decorator
