import sympy.physics.units as units
from spdm.util.logger import logger
from sympy.physics.units.systems.si import dimsys_SI


class Unit:
    """
        A `unit` of measurement is a standardised quantity of a physical property, 
        used as a factor to express occurring quantities of that property.
    """

    def __init__(self, unit=None, *args, **kwargs) -> None:
        if isinstance(unit, str):
            self._unit = getattr(units, unit, 1)
        else:
            self._unit = unit

    def serialize(self):
        return {}

    @staticmethod
    def deserialize(cls, d):
        return Unit(d)

    def __repr__(self) -> str:
        return f"{self._unit}"

    @property
    def is_dimensionless(self) -> bool:
        return self._unit is None or self.dimension == 1

    @staticmethod
    def calculate(ufunc, method,  *args, **kwargs):
        # FIXME (salmon 20210302): dimensional analysis
        return ufunc(*[((a._unit if a._unit is not None else 1) if isinstance(a, Unit) else (a or 1)) for a in args])

    @property
    def dimension(self):
        # dm = ufunc(*[getattr(u, "dimension", 1) for u in unit_list])
        # try:
        #     deps = dimsys_SI.get_dimensional_dependencies(dm)
        # except AttributeError:
        #     logger.error(f"Unit dismatch!  {dm} ")
        #     # raise TypeError(f"Unit dismatch! {ufunc.__name__}({dm})")
        return NotImplemented

    @property
    def valid(self):
        return self.dimension is not None
