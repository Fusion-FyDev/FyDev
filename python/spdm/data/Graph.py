from .Edge import Edge
from .Node import List, Dict, _TKey, _TObject

_TPath = List[_TKey]


class Graph(Dict[_TKey, _TObject]):
    """Represents '''Graph'''.
        * defines namespace for the '''Node'''s
        * Graph is a Node

        TODO (salmon 2019.7.25): add subgraph
    """

    def __init__(self, value=None, *args, **kwargs):
        super().__init__(value, *args, **kwargs)
        self._edges = []

    @property
    def edges(self) -> List[Edge]:
        return self._edges

    def link(self, source: _TPath, target: _TPath, *args, **kwargs):
        e = Edge(source, target, *args, graph=self, **kwargs)
        self._edges.append(e)
        return e


__SP_EXPORT__ = Graph
# class FunctionWrapperGraph(Graph):
#     def __init__(self, func, *args, **kwargs):
#         super().__init__(*args, signature=inspect.signature(func), **kwargs)


# def as_graph(func=None, **attrs):
#     def _decorate(wrapped):
#         @functools.wraps(wrapped)
#         def _wrapper(*args, **kwargs):
#             obj = None
#             if inspect.isfunction(wrapped):
#                 obj = FunctionWrapperActor(wrapped,  **attrs)
#             else:
#                 raise ValueError(f"Can not convert {wrapped} to Actor!")
#             obj.bind(*args, **kwargs)
#             return obj
#         return _wrapper

#     if func is None:
#         return _decorate
#     else:
#         return _decorate(func)
