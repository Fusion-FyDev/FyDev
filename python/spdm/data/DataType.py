from ..util.BiMap import BiMap
from enum import Enum


class DataTypeMapping(object):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def from_str(self, type_name):
        t = getattr(__builtins__, type_name, None)
        if isinstance(t, type):
            return t
    
