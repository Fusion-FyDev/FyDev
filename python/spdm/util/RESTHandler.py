import inspect
import collections


class RESTHandler:

    def put(self,  obj, path, value, *args, **kwargs):
        for p in path[:-1]:
            if type(p) is str and hasattr(obj, p):
                obj = getattr(obj, p)
            elif p in obj:
                obj = obj[p]
            else:
                obj[p] = {}
                obj = obj[p]
        if hasattr(obj, path[-1]):
            setattr(obj, path[-1], value)
        else:
            obj[path[-1]] = value

        # if len(path) > 0:
        #     raise path

        return None

    def get(self, obj, path, *args, **kwargs):
        for p in path:
            if type(p) is str and hasattr(obj, p):
                obj = getattr(obj, p)
            else:
                try:
                    obj = obj[p]
                except IndexError:
                    raise KeyError(path)
                except TypeError:
                    raise KeyError(path)
        return obj

    def delete(self, obj,  path, *args, **kwargs):
        if len(path) > 1:
            obj = self.get(obj,  path[:-1], *args, **kwargs)
        else:
            obj = self
        if hasattr(obj, path[-1]):
            delattr(obj, path[-1])
        else:
            del obj[path[-1]]

    def count(self, obj,  path, *args, **kwargs):
        obj = self.get(obj, path, *args, **kwargs)
        return len(obj)

    def contains(self, obj,  path, v, *args, **kwargs):
        obj = self.get(obj, path, *args, **kwargs)
        return v in obj

    def call(self, obj, path, *args, **kwargs):
        obj = self.get(obj, path)
        return obj(*args, **kwargs)

    @classmethod
    def wrap(cls, ops=None, **kwargs):
        if isinstance(ops, RESTHandler):
            return ops
        if ops is None and len(kwargs) > 0:
            ops = kwargs
        elif inspect.isfunction(ops):
            ops = {"get": ops}
        elif isinstance(ops, collections.abc.Mapping):
            pass
        else:
            return cls()

        n_cls = type(f"{cls.__name__}_rest",
                     (RESTHandler,), ops)
        return n_cls()
