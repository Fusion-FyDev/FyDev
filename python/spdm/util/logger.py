import logging
import logging.handlers
import inspect
import pathlib
import pprint
import os
import sys
from datetime import datetime


logger = logging.getLogger(__package__[:__package__.find('.')])

logger.setLevel(logging.DEBUG)

default_formater = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] '
                                     '%(pathname)s:%(lineno)d:%(funcName)s: '
                                     '%(message)s')


class CustomFormatter(logging.Formatter):
    """ Logging Formatter to add colors and count warning / errors """

    # Black       0;30     Dark Gray     1;30
    # Blue        0;34     Light Blue    1;34
    # Green       0;32     Light Green   1;32
    # Cyan        0;36     Light Cyan    1;36
    # Red         0;31     Light Red     1;31
    # Purple      0;35     Light Purple  1;35
    # Brown       0;33     Yellow        1;33
    # Light Gray  0;37     White         1;37

    grey = "\x1b[0;37m"
    blue = "\x1b[0;34m"
    yellow = "\x1b[1;33m"
    brown = "\x1b[0;33m"
    green = "\x1b[0;32m"
    red = "\x1b[0;31m"
    bold_red = "\x1b[1;31m"
    reset = "\x1b[0m"
    format_normal = '%(asctime)s %(levelname)s [%(name)s] %(pathname)s:%(lineno)d:%(funcName)s: %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format_normal + reset,
        logging.INFO:  blue + '%(asctime)s %(levelname)s [%(name)s] : %(message)s' + reset,
        logging.WARNING: brown + format_normal + reset,
        logging.ERROR: red + format_normal + reset,
        logging.CRITICAL: bold_red + format_normal + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def sp_enable_logging(handler=None, prefix=None, formater=None):

    # if prefix is None and isinstance(handler, str):
    #     prefix = handler
    #     handler = None
    formater = formater or CustomFormatter()

    if isinstance(handler, str) and handler == "STDOUT":
        handler = logging.StreamHandler(stream=sys.stdout)
    elif handler is None:
        prefix = prefix or os.environ.get('SP_LOG_PREFIX', f"/tmp/sp_log_{os.environ['USER']}/sp_")
        path = pathlib.Path(f"{prefix}{datetime.now().strftime(r'%Y%m%d_%H%M%S')}.log")
        path = path.expanduser().resolve()
        if not path.parent.exists():
            path.parent.mkdir(mode=0o0755, exist_ok=True)
        handler = logging.FileHandler(path)

    if issubclass(type(handler), logging.Handler):
        handler.setFormatter(formater or default_formater)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    else:
        raise NotImplementedError()


if not os.environ.get("SP_NO_DEBUG", None):
    sp_enable_logging("STDOUT")
    # sp_enable_logging()


def deprecated(func):

    def _wrap(func):
        def wrapped(*args, __fun__=func, ** kwargs):

            if inspect.isfunction(func):
                logger.warning(
                    f"Deprecated function '{__fun__.__qualname__}' !")
                raise DeprecationWarning(__fun__.__qualname__)
            else:
                logger.warning(f"Deprecated object {__fun__}")
            return __fun__(*args, **kwargs)
        return wrapped

    if func is None:
        return lambda o: _wrap(func)
    else:
        return _wrap(func)
