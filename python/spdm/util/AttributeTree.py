import collections
import copy
import pprint
from collections.abc import Mapping
import functools


class _NEXT_TAG_:
    pass


_next_ = _NEXT_TAG_()
_last_ = -1


class Dict:
    def __init__(self, data=None, *args,  default_factory=None, default_factory_array=None, **kwargs):
        super().__init__()
        self.__dict__['__data__'] = None
        self.__dict__['__default_factory__'] = default_factory or (lambda key: Dict())
        if callable(default_factory_array):
            self.__dict__['__default_factory_array__'] = default_factory_array
        else:
            self.__dict__['__default_factory_array__'] = Dict

        self.__update__(data)
        self.__update__(kwargs)

    def __missing__(self, key):
        return self.__as_object__().setdefault(key, self.__default_factory__(key))

    def __repr__(self):
        # if isinstance(self.__data__, collections.abc.Mapping):
        #     return pprint.pformat(self.__data__)

        if self.__data__ is None:
            return "<N/A>"
        else:
            return pprint.pformat(self.__data__)

    def __copy__(self):
        return Dict(copy.copy(self.__data__))

    def __deepcopy__(self, memo=None):
        return Dict(copy.deepcopy(self.__data__, memo))

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)

    def __getattr__(self, key):
        # res = getattr(self, key)
        if key.startswith('_'):
            res = self.__dict__[key]
        else:
            res = self.__getitem__(key)
        return res

    def __delattr__(self, key):
        if key in self.__dict__:
            del self.__dict__[key]
        elif isinstance(self.__data__, collections.abc.Mapping) and key in self.__data__:
            del self.__data__[key]

    def __getitem__(self, key):
        res = None
        if isinstance(key, list):
            res = self
            for k in key:
                v = getattr(res, k, None)
                if v is None:
                    try:
                        v = res.__getitem__(k)
                    except Exception as error:
                        raise error
                    else:
                        res = v
                else:
                    res = v
        elif isinstance(key, str):
            res = getattr(self.__class__, key, None)
            if res is None:
                res = self.__as_object__().get(key, None)
            elif isinstance(res, property):
                res = getattr(res, "fget")(self)
            elif isinstance(res, functools.cached_property):
                res = res.__get__(self)
        elif key is _next_:
            res = self.__push_back__()
        elif type(key) in (int, slice, tuple):
            if self.__data__ is None or isinstance(self.__data__, list):
                res = self.__as_array__()[key]
            elif key == 0:
                res = self.__data__
            else:
                raise KeyError(f"Can not insert key '{key}'!  {type(self.__data__)} \n error:{error}")

        return res if res is not None else self.__missing__(key)

    def __normalize__(self, value, name=None):
        return value

    def __setitem__(self, key, value):
        if isinstance(key, str) and '.' in key:
            key = key.split('.')

        if isinstance(key, list):
            self.__getitem__(key[:1]).__setitem__(key[-1], value)
        elif key is _next_:
            self.__push_back__().__update__(self.__normalize__(value, key))
        elif isinstance(value, Mapping):
            self.__delitem__(key)
            self.__getitem__(key).__update__(self.__normalize__(value, key))
        elif isinstance(key, str):
            self.__as_object__().__setitem__(key, self.__normalize__(value, key))
        elif type(key) in (int, slice, tuple):
            self.__as_array__()[key] = self.__normalize__(value, key)

        else:
            raise TypeError(f"Illegal key type! {type(key)}")

    def __delitem__(self, key):

        if isinstance(self.__data__, collections.abc.Mapping) or isinstance(self.__data__, collections.abc.Sequence):
            try:
                del self.__data__[key]
            except KeyError:
                pass

    def __contain__(self, key):
        if self.__data__ is None:
            return False
        elif isinstance(key, str):
            return key in self.__data__
        elif type(key) is int:
            return key < len(self.__data__)
        else:
            raise KeyError(key)

    def __len__(self):
        if self.__data__ is None:
            return 0
        else:
            return len(self.__data__)

    def __iter__(self):
        if self.__data__ is None:
            return
        elif isinstance(self.__data__,  collections.abc.Mapping):
            for k, v in self.__data__.items():
                if isinstance(v, collections.abc.Mapping):
                    v = Dict(v)

                yield k, v
        else:
            for v in self.__data__:
                if isinstance(v, collections.abc.Mapping):
                    v = Dict(v)
                yield v

    def __as_native__(self):
        if isinstance(self.__data__, collections.abc. Mapping):
            res = {}
            for k, v in self.__data__.items():
                if isinstance(v, Dict):
                    res[k] = v.__as_native__()
                else:
                    res[k] = v
        else:
            res = []
            for v in self.__data__:
                if isinstance(Dict):
                    res.append(v.__as_native__())
                else:
                    res.append(v)
        return res

    def __as_object__(self):
        if isinstance(self.__data__, collections.abc.Mapping):
            pass
        elif self.__data__ is None:
            self.__data__ = dict()
        else:
            raise TypeError(f"Can not create 'object': node is not empty! {type(self.__data__)}")
        return self.__data__

    def __as_array__(self):
        if isinstance(self.__data__, list):
            pass
        elif self.__data__ is None or len(self.__data__) == 0:
            self.__data__ = list()
        else:
            raise TypeError(f"Can not create 'list': node is not empty! ")

        return self.__data__

    def __push_back__(self, value=None):
        self.__as_array__().append(value or self.__default_factory_array__())
        return self.__data__[-1]

    def __pop_back__(self):
        if not isinstance(self.__data__, list):
            raise IndexError(f"Can push data to 'Object' ")
        self.__data__.pop()

    def __update__(self, other):
        if other is None:
            return
        elif isinstance(other, Dict):
            other = other.__data__

        if isinstance(other, collections.abc.Mapping):
            if len(other) == 0 and isinstance(self.__data__, list):
                return
            obj = self.__as_object__()
            for k, v in other.items():
                v = self.__normalize__(v, k)
                if isinstance(v, collections.abc.Mapping):
                    d = self.__missing__(k)
                    if isinstance(d, Dict):
                        d.__update__(v)
                    elif isinstance(d, collections.abc.Sequence):
                        if isinstance(v, collections.abc.Sequence) and not isinstance(v, str):
                            d.extend(v)
                        else:
                            d.append(v)
                elif isinstance(v, Dict) and v.__data__ is None:
                    pass
                else:
                    obj[k] = v
        elif isinstance(other, collections.abc.Sequence):
            if len(other) == 0 and self.__data__ is not None:
                return
            obj = self.__as_array__()
            for v in other:
                if isinstance(v, Dict):
                    obj.append(v)
                elif isinstance(v, collections.abc.Mapping) or isinstance(v, collections.abc.Sequence):
                    obj.append(Dict(v))
                else:
                    obj.append(v)
        else:
            raise TypeError(f"Not supported operator! update({type(self.__data__)},{type(other)})")

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            return None
        new = self.__class__(self)
        new.__update__(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, dict):
            return None
        new = self.__class__(self)
        new.__update__(self)
        return new

    def __ior__(self, other):
        self.__update__(other)
        return self

    def __bool__(self):
        return self.__data__ is not None and len(self.__data__) > 0


class Foo(Dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foo(*args, **kwargs)

    def foo(self, *args, **kwargs):
        print(self.__data__)


if __name__ == "__main__":
    a = Foo()
    a.b.c.d = 5
    # pprint.pprint(a)

    # pprint.pprint(a.b.f)
    a.foo()

    d = a.b.f.__push_back__()
    d.text = "hellow world"
    a.b.f.__push_back__(5)

    a.g.h = {"b": 1, "z": {"t": 1}}
    # pprint.pprint(a)

    pprint.pprint(a.g.h)
    pprint.pprint(a.g.h.w or 123.5)

    a.g.h |= {"y": 5, "z": {"x": 6}}

    pprint.pprint(a.g.h)

    pprint.pprint(a)
    pprint.pprint(len(a.b.f))

    # @property
    # def entry(self):
    #     return LazyProxy(self)
    # class __lazy_proxy__:
    #     @staticmethod
    #     def put(obj, path, value, *args, **kwargs):
    #         if len(path) == 0:
    #             raise KeyError("Empty path")
    #         for idx, p in enumerate(path[:-1]):
    #             if isinstance(obj, Dict):
    #                 obj = obj.setdefault(p, Dict())
    #             elif not isinstance(p, str) and isinstance(obj, list):
    #                 obj = obj[p]
    #             else:
    #                 raise KeyError(".".join(path[:idx+1]))
    #         if hasattr(obj, path[-1]):
    #             setattr(obj, path[-1], value)
    #         else:
    #             obj[path[-1]] = value

    #         # if len(path) > 0:
    #         #     raise path

    #         return None

    #     @staticmethod
    #     def get(obj, path,  *args, **kwargs):
    #         if len(path) == 0:
    #             return obj

    #         for idx, p in enumerate(path):
    #             if isinstance(obj, Dict):
    #                 obj = obj.get(p, None)
    #             elif isinstance(obj, list):
    #                 try:
    #                     obj = obj[p]
    #                 except IndexError:
    #                     obj = None
    #             else:
    #                 obj = getattr(obj, p, None)

    #             if obj is None:
    #                 raise KeyError(f"Illegal path '{'.'.join(path[:idx+1])}'! ")

    #         return obj

    #     @staticmethod
    #     def get_value(data, path, *args, **kwargs):
    #         return Dict.__lazy_proxy__.get(data, path, *args, **kwargs)

    #     @staticmethod
    #     def delete(data,  path, *args, **kwargs):
    #         if len(path) > 1:
    #             obj = Dict.__lazy_proxy__.get(data, path[:-1], *args, **kwargs)
    #         else:
    #             obj = data
    #         if hasattr(obj, path[-1]):
    #             delattr(obj, path[-1])
    #         else:
    #             del obj[path[-1]]

    #     @staticmethod
    #     def push_back(data,  path, value, *args, **kwargs):
    #         # if len(path) == 0:
    #         #     data.push_back(value)
    #         # else:
    #         # data.get(path).setdefault(path[-1], []).append(value)
    #         if len(path) > 0:
    #             obj = Dict.__lazy_proxy__.get(data, path[:-1]).setdefault(path[-1], [])
    #         else:
    #             obj = data

    #         obj.append(value or Dict())
    #         return path+[len(obj)-1]

    #     @staticmethod
    #     def count(data,  path, *args, **kwargs):
    #         obj = Dict.__lazy_proxy__.get(data, path, *args, **kwargs)
    #         return len(obj)

    #     @staticmethod
    #     def contains(data,  path, v, *args, **kwargs):
    #         obj = Dict.__lazy_proxy__.get(data, path, *args, **kwargs)
    #         return v in obj

    #     @staticmethod
    #     def iter(data,  path, *args, **kwargs):
    #         for obj in Dict.__lazy_proxy__.get(data, path, *args, **kwargs):
    #             if type(obj) in (int, float, str):
    #                 yield obj
    #             else:
    #                 yield LazyProxy(obj)

    #     @staticmethod
    #     def call(data, path, *args, **kwargs):
    #         obj = Dict.__lazy_proxy__.get(data, path)
    #         if callable(obj):
    #             return obj(*args, **kwargs)
    #         elif len(args)+len(kwargs) == 0:
    #             return obj
    #         else:
    #             raise TypeError(f"{obj.__class__.__name__} is not callable")
