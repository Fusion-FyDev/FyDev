
import numpy as np
from spdm.util.logger import logger


class DObject(np.ndarray):

    @staticmethod
    def __new__(cls, value=None, *args, shape=None,  dtype=None, order=None,   **kwargs):

        if value is not None:
            obj = np.asarray(value, dtype=dtype, order=order).view(cls)
        elif shape is not None:
            obj = np.ndarray(shape, dtype=dtype, order=order, **kwargs).view(cls)
        else:
            obj = None

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

    def __init__(self,  *args, **kwargs):
        logger.debug(self.__class__.__name__)

    def __array__(self):
        return self.view(np.ndarray)

    def __array_ufunc__(self, ufunc, method, *inputs, out=None, **kwargs):
        if method != '__call__':
            return NotImplemented

        return ufunc(*[(arg.__array__() if hasattr(arg, "__array__") else arg) for arg in inputs], **kwargs)

    @property
    def is_scalar(self):
        return isinstance(self._value, np.ndarray) or self._value.shape == ()

    @property
    def value(self):
        return self.__array__()


# class DObjectFunction(DObject):

#     def __init__(self, ufunc,   *args,  **kwargs):
#         super().__init__(*args, **kwargs)

#         if not callable(ufunc):
#             raise TypeError(type(ufunc))
#         elif not isinstance(ufunc, np.ufunc):
#             ufunc = np.vectorize(ufunc)
#         self._ufunc = ufunc

#     def __call__(self, x=None):
#         if x is None:
#             x = self._axis
#         if x is None:
#             raise ValueError(f" x is None !")

#         res = self._ufunc(x)
#         if isinstance(res, np.ndarray) and not isinstance(res, DObject):
#             res = res.view(DObject)
#             res._axis = x
#         return res

#     def __getitem__(self, idx):
#         return self._ufunc(self._axis[idx])

#     @property
#     def value(self):
#         if self.shape == ():
#             try:
#                 self.resize(self._axis.size, refcheck=True)
#                 self.reshape(self._axis.shape)
#             except Exception:
#                 res = self._ufunc(self._axis)
#             else:
#                 np.copyto(self, self._ufunc(self._axis))
#                 res = self.view(np.ndarray)
#         else:
#             res = self.view(np.ndarray)
#         return res

#     @cached_property
#     def derivative(self):
#         return DObject(np.gradient(self.value)/np.gradient(self._axis), axis=self._axis)

#     @cached_property
#     def dln(self, *args, **kwargs):
#         r"""
#             .. math:: d\ln f=\frac{df}{f}
#         """
#         return DObject(self.derivative.value/self.value, axis=self._axis)

#     @cached_property
#     def integral(self):
#         data = scipy.integrate.cumtrapz(self[:], self.axis[:], initial=0.0)
#         return DObject(data, axis=self.axis)

#     @cached_property
#     def inv_integral(self):
#         value = scipy.integrate.cumtrapz(self[::-1], self.axis[::-1], initial=0.0)[::-1]
#         return DObject(value, axis=self.axis)


# class DObjectExpression(DObject):

#     def __init__(self,    func,   *args, func_args=None, func_kwargs=None,  **kwargs):
#         self._func = func
#         self._args = func_args or []
#         self._kwargs = func_kwargs or {}
#         super().__init__(*args, **kwargs)

#     def __str__(self):
#         return self.__repr__()

#     def __repr__(self):
#         return f"<{self.__class__.__name__} ufunc={self._func}  >"

#     def __call__(self, x_axis=None):
#         if x_axis is None:
#             x_axis = self._axis
#         args = []
#         for arg in self._args:
#             if isinstance(arg,  DObject):
#                 data = arg(x_axis)
#             else:
#                 data = arg
#             if isinstance(data, DObject):
#                 args.append(data.view(np.ndarray))
#             else:
#                 args.append(data)

#         res = self._func(*args, **self._kwargs)

#         if isinstance(res, np.ndarray) and res.shape != () and (any(np.isnan(res)) or any(np.isinf(res))):
#             raise ValueError(res)

#         if isinstance(res, np.ndarray) and not isinstance(res, DObject):
#             res = res.view(DObject)
#             res._axis = x_axis

#         return res

#     def __getitem__(self, idx):
#         args = []
#         if not hasattr(self, "_args"):
#             return self.view(np.ndarray)[idx]

#         for arg in self._args:
#             if not isinstance(arg,  np.ndarray):
#                 args.append(arg)
#             elif not isinstance(arg, DObject):
#                 args.append(arg[idx])
#             elif arg.axis is self.axis:
#                 args.append(arg[idx])
#             else:
#                 data = arg(self._axis[idx])
#                 if isinstance(data, np.ndarray):
#                     args.append(data.view(np.ndarray))
#                 else:
#                     args.append(data)

#         return self._func(*args, **self._kwargs)

#     def __setitem__(self, idx, value):
#         if self.shape != self._axis.shape:
#             self.evaluate()
#         self.view(np.ndarray)[idx] = value

#     def evaluate(self):
#         if self.shape != self._axis.shape:
#             self.resize(self._axis.size, refcheck=False)
#             self.reshape(self._axis.shape)
#         np.copyto(self, self[:])

#     @property
#     def value(self):
#         return self[:]
