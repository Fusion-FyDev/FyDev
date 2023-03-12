from functools import cached_property

import numpy as np
import scipy.interpolate
from scipy.interpolate.interpolate import PPoly

from ..util.logger import logger

# from ..data.Quantity import Quantity

# if version.parse(scipy.__version__) <= version.parse("1.4.1"):
#     from scipy.integrate import cumtrapz as cumtrapz
# else:
#     from scipy.integrate import cumulative_trapezoid as cumtrapz

logger.debug(f"SciPy: Version {scipy.__version__}")


class PimplFunc(object):
    def __init__(self,  *args,   ** kwargs) -> None:
        super().__init__()

    @property
    def is_periodic(self):
        return False

    @property
    def x(self) -> np.ndarray:
        return NotImplemented

    @property
    def y(self) -> np.ndarray:
        return self.apply(self.x)

    def apply(self, x) -> np.ndarray:
        raise NotImplementedError(self.__class__.__name__)

    @cached_property
    def derivative(self):
        return SplineFunction(self.x, self.y, is_periodic=self.is_periodic).derivative

    @cached_property
    def antiderivative(self):
        return SplineFunction(self.x, self.y, is_periodic=self.is_periodic).antiderivative

    def invert(self, x=None):
        x = self.x if x is None else x
        return PimplFunc(self.apply(x), x)


class WrapperFunc(PimplFunc):
    def __init__(self, x, func, * args,   ** kwargs) -> None:
        super().__init__()
        self._x = x
        self._func = func

    def apply(self, x) -> np.ndarray:
        x = self.x if x is None else x
        return self._func(x)

    @property
    def x(self) -> np.ndarray:
        return self._x


class SplineFunction(PimplFunc):
    def __init__(self, x, y=None, is_periodic=False,  ** kwargs) -> None:
        super().__init__()
        self._is_periodic = is_periodic

        if isinstance(x, PPoly) and y is None:
            self._ppoly = x
        elif not isinstance(x, np.ndarray) or y is None:
            raise TypeError((type(x), type(y)))
        else:
            if callable(y):
                y = y(x)
            elif isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
                assert(x.shape == y.shape)
            elif isinstance(y, (float, int)):
                y = np.full(len(x), y)
            else:
                raise NotImplementedError(f"Illegal input {[type(a) for a in args]}")

            if is_periodic:
                self._ppoly = scipy.interpolate.CubicSpline(x, y, bc_type="periodic", **kwargs)
            else:
                self._ppoly = scipy.interpolate.CubicSpline(x, y, **kwargs)

    @property
    def x(self) -> np.ndarray:
        return self._ppoly.x

    @cached_property
    def derivative(self):
        return SplineFunction(self._ppoly.derivative())

    @cached_property
    def antiderivative(self):
        return SplineFunction(self._ppoly.antiderivative())

    def apply(self, x) -> np.ndarray:
        x = self.x if x is None else x
        return self._ppoly(x)

    def integrate(self, a, b):
        return self._ppoly.integrate(a, b)


class PiecewiseFunction(PimplFunc):
    def __init__(self, x, cond, func, *args,    **kwargs) -> None:
        super().__init__()
        self._x = x
        self._cond = cond
        self._func = func

    @property
    def x(self) -> np.ndarray:
        return self._x

    def apply(self, x) -> np.ndarray:
        cond = [c(x) for c in self._cond]
        return np.piecewise(x, cond, self._func)


class Expression(PimplFunc):
    def __init__(self, ufunc, method, *inputs,  **kwargs) -> None:
        super().__init__()
        self._ufunc = ufunc
        self._method = method
        self._inputs = inputs
        self._kwargs = kwargs

    @property
    def is_periodic(self):
        return all([d.is_periodic for d in self._inputs if isinstance(d, Function)])

    @property
    def x(self):
        return next(d.x for d in self._inputs if isinstance(d, Function))

    @property
    def y(self) -> np.ndarray:
        return self.apply(self.x)

    def apply(self, x) -> np.ndarray:
        def wrap(x, d):
            if isinstance(d, Function):
                res = d(x).view(np.ndarray)
            elif not isinstance(d, np.ndarray):
                res = d
            elif d.shape == self.x.shape:
                res = Function(self.x, d)(x).view(np.ndarray)
            else:
                raise ValueError(f"{self.x.shape} {d.shape}")

            return res

        if self._method != "__call__":
            op = getattr(self._ufunc, self._method)
            # raise RuntimeError((self._ufunc, self._method))
            res = op(*[wrap(x, d) for d in self._inputs])
        try:
            res = self._ufunc(*[wrap(x, d) for d in self._inputs])
        except Warning as error:
            raise ValueError(
                f"\n {self._ufunc}  {[type(a) for a in self._inputs]}  {[a.shape for a in self._inputs if isinstance(a,Function)]} {error} \n ")
        return res


class Function(np.ndarray):
    def __new__(cls, x, y=None, *args,   experiment=False, **kwargs):
        if cls is not Function:
            return object.__new__(cls, *args, **kwargs)

        pimpl = None
        x0 = None
        y0 = None

        if y is None:
            if isinstance(x, Function):
                pimpl = x._pimpl
                y0 = x.view(np.ndarray)
                x0 = x.x
            elif isinstance(x, PimplFunc):
                pimpl = x
                y0 = pimpl.y
                x0 = pimpl.x
            elif isinstance(x, np.ndarray):
                y0 = x
        elif not isinstance(x, np.ndarray):
            raise TypeError(f"x should be np.ndarray not {type(x)}!")
        elif isinstance(y, Function):
            if x is y._x:
                pimpl = y._pimpl
                y0 = y.view(np.ndarray)
                x0 = x
            else:
                pimpl = y._pimpl
                y0 = y(x, *args, **kwargs)
                x0 = x
        elif isinstance(y, PimplFunc):
            pimpl = y
            y0 = pimpl.apply(args[0], *args[2:], **kwargs)
            x0 = x
        elif isinstance(y, np.ndarray):
            if(getattr(x, "shape", None) != getattr(y, "shape", None)):
                raise RuntimeError((getattr(x, "shape", None), getattr(y, "shape", None)))
            pimpl = None
            x0 = x
            y0 = y
        elif y == None:
            pimpl = None
            x0 = x
            y0 = np.zeros(x.shape)
        elif isinstance(y, (int, float, complex)):
            def pimpl(x, _v=y): return _v if not isinstance(x, np.ndarray) else np.full(x.shape, _v)
            x0 = x
            y0 = np.full(x.shape, y)
        elif callable(y):
            pimpl = WrapperFunc(x, y, *args, **kwargs)
            y0 = pimpl.apply(x)
            x0 = pimpl.x
        elif len(args) > 0 and isinstance(y, list) and isinstance(args[0], list):
            pimpl = PiecewiseFunction(x, y, *args, **kwargs)
            y0 = pimpl.apply(x)
            x0 = pimpl.x

        if isinstance(x0, np.ndarray) and isinstance(y0, np.ndarray) and x0.shape == y0.shape:
            obj = y0.view(cls)
            obj._pimpl = pimpl
            obj._x = x0
        else:
            raise RuntimeError(f"{type(x)}   {type(y)} ")

        return obj

    def __array_finalize__(self, obj):
        self._pimpl = getattr(obj, '_pimpl', None)
        self._x = getattr(obj, '_x', None)

    def __array_ufunc__(self, ufunc, method, *inputs,   **kwargs):
        return Function(Expression(ufunc, method, *inputs, **kwargs))

    def __init__(self, *args, is_periodic=False, **kwargs):
        self._is_periodic = is_periodic

    def __getitem__(self, key):
        d = super().__getitem__(key)
        if isinstance(d, np.ndarray) and len(d.shape) > 0:
            d = d.view(Function)
            d._pimpl = self._pimpl
            d._x = self.x[key]
        return d

    @cached_property
    def spl(self):
        if isinstance(self._pimpl, SplineFunction):
            return self._pimpl
        else:
            return SplineFunction(self.x, self.view(np.ndarray), is_periodic=self.is_periodic)

    @property
    def is_periodic(self):
        return self._is_periodic

    @property
    def x(self):
        return self._x

    @cached_property
    def derivative(self):
        return Function(self.spl.derivative)

    @cached_property
    def antiderivative(self):
        return Function(self.spl.antiderivative)

    @cached_property
    def invert(self):
        return Function(self.spl.invert(self._x))

    def pullback(self, *args, **kwargs):
        if len(args) == 0:
            raise ValueError(f"missing arguments!")
        elif len(args) == 2 and args[0].shape == args[1].shape:
            x0, x1 = args
            y = self(x0)
        elif isinstance(args[0], Function) or callable(args[0]):
            logger.warning(f"FIXME: not complete")
            x1 = args[0](self.x)
            y = self.view(np.ndarray)
        elif isinstance(args[0], np.ndarray):
            x1 = args[0]
            y = self(x1)
        else:
            raise TypeError(f"{args}")

        return Function(x1, y, is_periodic=self.is_periodic)

    def integrate(self, a=None, b=None):
        return self.spl.integrate(a or self.x[0], b or self.x[-1])

    def __call__(self,   *args, **kwargs):
        if len(args) == 0:
            args = [self._x]
        if hasattr(self._pimpl, "apply"):
            res = self._pimpl.apply(*args, **kwargs)
        elif callable(self._pimpl):
            res = self._pimpl(*args, **kwargs)
        else:
            res = self.spl.apply(*args, **kwargs)
            # raise RuntimeError(f"{type(self.spl)}")

        return res.view(np.ndarray)


def create_ppoly(x, y, * args, **kwargs):

    ppoly = scipy.interpolate.CubicSpline(x, y, **kwargs)

    return ppoly


class Function2(object):
    def __init__(self, x, y, dy=None, *args, **kwargs) -> None:
        super().__init__()
        # super().__init__(*args, **kwargs)
        self._x = x
        self._y = y
        self._kwargs = kwargs

    @property
    def x(self):
        return self._ppoly.x

    @cached_property
    def y(self):
        return self._ppoly(self.x)

    @cached_property
    def _ppoly(self):
        return create_ppoly(self._x, self._y, **self._kwargs)

    def rms_rediusal(self, x=None, reference=None):
        return NotImplemented

    def discontinue(self, x, left=None, right=None):
        return NotImplemented

    def insert(self, pts):
        raise NotImplementedError()

    def refine(self, tol=1.0e-3, weight=None):
        insert_1, = np.nonzero((rms_res > tol) & (rms_res < 100 * tol))
        insert_2, = np.nonzero(rms_res >= 100 * tol)
        nodes_added = insert_1.shape[0] + 2 * insert_2.shape[0]

        if m + nodes_added > max_nodes:
            status = 1
            if verbose == 2:
                nodes_added = "({})".format(nodes_added)
                print_iteration_progress(iteration, max_rms_res, max_bc_res,
                                         m, nodes_added)

        if verbose == 2:
            print_iteration_progress(iteration, max_rms_res, max_bc_res, m,
                                     nodes_added)

        if nodes_added > 0:
            x = modify_mesh(x, insert_1, insert_2)
            h = np.diff(x)
            y = sol(x)
        elif max_bc_res <= bc_tol:
            status = 0

        elif iteration >= max_iteration:
            status = 3

        return NotImplemented

    def coarsen(self, tol=1.0e-3, weight=None):
        raise NotImplementedError()
