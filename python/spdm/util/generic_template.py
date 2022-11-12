
import typing
from .logger import logger


def get_template_args(obj, idx=None):
    o_cls = getattr(obj, "__orig_class__", None)

    logger.debug(dir(obj))
    logger.debug(obj.__dict__)

    if o_cls is None:
        return None
    idx = idx or 0
    args = typing.get_args(o_cls)
    if len(args) < idx:
        return None
    else:
        return args[0]
