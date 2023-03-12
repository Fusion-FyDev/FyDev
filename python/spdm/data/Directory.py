import contextlib
import io
import pathlib
import shutil
import tempfile
import uuid

from spdm.util.logger import logger
from spdm.util.urilib import urisplit
from .Document import Document
from .DataObject import DataObject


class Directory(DataObject):
    """ Default entry for file-like object
    """

    def __init__(self,  desc, value=None, *args, **kwargs):
        pass
