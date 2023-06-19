import time
import logging
from typing import Union, Tuple, Type
from DataSource.Exceptions import MaxRetriesReachedError


logger = logging.getLogger(__name__)


def exponential_backoff(max_val=600):
    i = 1    
    while True:
        t = 2 ** i
        if t < max_val:
            yield t
            i += 1
        else:
            yield max_val


def retry(times:int, exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]], max_wait_time=600):
    """
    Retries the decorated function/method `times` times if the exceptions listed
    in ``exceptions`` are thrown. Uses exponential backoff between runs.

    Parameters
    ----------
    times : int     
        The number of times to repeat the wrapped function/method

    exceptions :  Union[Type[Exception], Tuple[Type[Exception], ...]
        Lists of exceptions that trigger a retry attempt
    """
    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            wait_time_gen = exponential_backoff(max_wait_time)
            while attempt < times:
                t = next(wait_time_gen)
                time.sleep(t)
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.exception(
                        'Exception thrown when attempting to run %s, attempt '
                        '%d of %d' % (func, attempt+1, times),
                    )
                    attempt += 1

                    if attempt == times:
                        raise MaxRetriesReachedError(f"Failed after retrying {times} times.") from e
        return newfn
    return decorator