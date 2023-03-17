import collections
import os
import pathlib
import shlex
import subprocess
import traceback
import uuid
import sys

class StandardModule:
    '''Module wrapper.
    Decompose a complete physical module to obtain name, version and tag.
    This class represents internally a module. Concrete module system
    implementation should deal only with that.

    :meta private:
    '''

    def __init__(self, name, collection=False, path=None):
        if not isinstance(name, str):
            raise TypeError('module name not a string')

        name = name.strip()
        if not name:
            raise ValueError('module name cannot be empty')

        try:
            self._name, self._versiontag = name.split('/', maxsplit=1)
            self._version, self._tag =self._versiontag.split('-', maxsplit=1)
        except ValueError:
            self._name, self._version,self._tag = name, None,None

        self._path = path

        # This module represents a "module collection" in TMod4
        self._collection = collection

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def versiontag(self):
        return self._versiontag

    @property
    def tag(self):
        return self._tag      

    @property
    def collection(self):
        return self._collection

    @property
    def path(self):
        return self._path

    @property
    def fullname(self):
        if self.versiontag is not None:
            return '/'.join((self.name, self.versiontag))
        else:
            return self.name

    @property
    def fullmodulename(self):
        if self.versiontag is not None:
            return '-'.join((self.name, self.versiontag))
        else:
            return self.name

    def __hash__(self):
        # Here we hash only over the name of the module, because foo/1.2 and
        # simply foo compare equal. In case of hash conflicts (e.g., foo/1.2
        # and foo/1.3), the equality operator will resolve it.
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        if self.path != other.path:
            return False

        if self.collection != other.collection:
            return False

        if not self.version or not other.version:
            return self.name == other.name
        else:
            return self.name == other.name and self.version == other.version

    def __repr__(self):
        return (f'{type(self).__name__}({self.fullname}, '
                '{self.collection}, {self.path})')

    def __str__(self):
        return self.fullname




