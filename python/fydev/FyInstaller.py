from spdm.util.logger import logger


class FyInstaller(object):
    _registry = {}

    @classmethod
    def register(cls, name):
        """ Register a new installer.
        :param name: Name of the installer.
        :return: Decorator function.
        """
        def _register(installer):
            if name in cls._registry:
                raise ValueError(f"Installer {name} already registered.")
            cls._registry[name] = installer
            return installer
        return _register

    @classmethod
    def create(cls, name, *args, **kwargs):
        """ Create a new installer.
        :param name: Name of the installer.
        :return: New installer.
        """
        if name not in cls._registry:
            raise ValueError(f"Installer {name} not registered.")
        return cls._registry[name](*args, **kwargs)

    def __init__(self, *args, package=None, **kwargs) -> None:
        super().__init__()
        self._package = package  # type: FyPackage

    def install(self, *args, **kwargs):
        logger.debug(f"Installing package {self._package.tag.name}...")
        raise NotImplementedError("Install method not implemented.")
