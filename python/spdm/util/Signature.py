import collections
import inspect

from .logger import logger


class Signature(inspect.Signature):

    @staticmethod
    def _create_annotation(s):
        if type(s) is str:
            return getattr(__builtins__, s, {"type": s})
        elif isinstance(s, type):
            return s
        elif s is None:
            return inspect.Signature.empty
        else:
            # elif isinstance(s, collections.abc.Mapping):
            return s
        # else:
        #     raise TypeError(f"Illegal annotation type! {s}")

    @staticmethod
    def _create_parameter(p, default_kind="KEYWORD_ONLY"):
        if isinstance(p, inspect.Parameter):
            return p
        elif isinstance(p, collections.abc.Mapping):
            return inspect.Parameter(
                p.get("name"),
                inspect._ParameterKind[p.get("kind", default_kind)].value,
                default=p.get("default", inspect.Parameter.empty),
                annotation=Signature._create_annotation(
                    p.get("dtype", p.get("annotation", None)))
            )

    def __init__(self, parameters=None, *, return_annotation=inspect.Signature.empty, default_kind="KEYWORD_ONLY"):

        if type(parameters) is not str and isinstance(parameters, collections.abc.Sequence):
            parameters = [Signature._create_parameter(
                p, default_kind=default_kind) for p in parameters]
        elif isinstance(parameters, collections.abc.Mapping):
            parameters = [Signature._create_parameter(
                p, default_kind=default_kind) for p in parameters.values()]

        super().__init__(parameters=parameters,
                         return_annotation=Signature._create_annotation(return_annotation))

    @classmethod
    def create(cls,  parameters=None, return_annotation=None, **kwargs):
        # assert(type(parameters) is not str and isinstance(
        #     parameters, collections.abc.Sequence))
        # parameters = [p for p in parameters if p.get("direction", "IN") != "OUT"]

        if return_annotation is None:
            pass
        elif isinstance(return_annotation, collections.abc.Sequence) and len(return_annotation) == 1:
            return_annotation = return_annotation[0]

        return cls(parameters, return_annotation=return_annotation, **kwargs)

    @classmethod
    def from_callable(cls, func, *args, **kwargs):
        try:
            sig = super(Signature, cls).from_callable(func)
        except:
            if hasattr(func, "__call__"):
                sig = super(Signature, cls).from_callable(func.__call__)
            else:
                raise TypeError(f"Can not get signature from {type(func)}!")
        return sig
