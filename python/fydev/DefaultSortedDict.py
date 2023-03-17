import sortedcontainers


class DefaultSortedDict(sortedcontainers.SortedDict):
    # 继承SortedDict类，并添加默认工厂函数
    def __init__(self, default_factory=None, *args, **kwargs):
        if default_factory is not None and not callable(default_factory):
            raise TypeError('first argument must be callable')
        super().__init__(*args, **kwargs)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __setitem__(self, key, value):
        # 检查值是否是default_factory的对象，如果不是，抛出异常
        if not isinstance(value, self.default_factory):
            raise TypeError(f'value must be a {self.default_factory.__name__} object')
        super().__setitem__(key, value)
