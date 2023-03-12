
from spdm.util.logger import logger

from .DObject import DObject
from .Node import Node


class DataSet(DObject, Node):

    def __init__(self,  *args, name=None, parent=None,  **kwargs):
        Node.__init__(self, name, parent)
        DObject.__init__(self, *args, **kwargs)

    # @property
    # def is_scalar(self):
    #     return isinstance(self._value, np.ndarray) or self._value.shape == ()

    # @property
    # def is_dimensionless(self):
    #     return self._unit is None or self._unit.is_dimensionless
