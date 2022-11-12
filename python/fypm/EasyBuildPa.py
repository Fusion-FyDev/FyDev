import collections
import os
import sys
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
from pathlib import Path,PurePosixPath
import shlex
import subprocess
import signal
import traceback
import uuid
import re
import abc 

from spdm.util.logger import logger

from spdm.flow.ModuleRepository import ModuleRepository
import fypm.typecheck as typ
import pprint

class change_dir:
    '''Context manager to temporarily change the current working directory.

    :arg dir_name: The directory to temporarily change to.
    '''

    def __init__(self, dir_name):
        self._wd_save = os.getcwd()
        self._dir_name = dir_name

    def __enter__(self):
        os.chdir(self._dir_name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._wd_save)

class Field:
    '''Base class for attribute validators.'''

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        try:
            return obj.__dict__[self._name]
        except KeyError:
            # We raise an AttributeError to emulate the standard attribute
            # access.
            raise AttributeError("%s object has no attribute '%s'" %
                                 (objtype.__name__, self._name)) from None

    def __set__(self, obj, value):
        obj.__dict__[self._name] = value


class TypedField(Field):
    '''Stores a field of predefined type'''

    def __init__(self, main_type, *other_types):
        self._types = (main_type,) + other_types
        if not all(isinstance(t, type) for t in self._types):
            raise TypeError('{0} is not a sequence of types'.
                            format(self._types))

    def _check_type(self, value):
        if not any(isinstance(value, t) for t in self._types):
            typedescr = '|'.join(t.__name__ for t in self._types)
            raise TypeError(
                "failed to set field '%s': '%s' is not of type '%s'" %
                (self._name, value, typedescr))

    def __set__(self, obj, value):
        self._check_type(value)
        super().__set__(obj, value)

class BuildSystem(abc.ABC):
    '''The abstract base class of any build system.
    Maybe include :
    - Make : make -j [N] [-f MAKEFILE] [-C SRCDIR] CC="X" CXX="X" FC="X" NVCC="X" CPPFLAGS="X" CFLAGS="X" CXXFLAGS="X" FCFLAGS="X" LDFLAGS="X" OPTIONS
    - SingleSource: COMPILER CPPFLAGS XFLAGS SRCFILE -o EXEC LDFLAGS
    - configured-based : ./configure ....
    - Cmake(configured-based) : cmake ...
    - Autotools-based(configured-based) : ./configure ;make ;make install 
    - EasyBuild : In our system ,use the EasyBuild to build and install the code in the build stage .
    Concrete build systems inherit from this class and must override the
    :func:`emit_build_commands` abstract function.
    '''

    #: The C compiler to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the compiler defined in the current programming environment will be
    #: used.
    #:
    #: :type: :class:`str`
    #: :default: ``''``
    cc  = TypedField(str)

    #: The C++ compiler to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the compiler defined in the current programming environment will be
    #: used.
    #:
    #: :type: :class:`str`
    #: :default: ``''``
    cxx = TypedField(str)

    #: The Fortran compiler to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the compiler defined in the current programming environment will be
    #: used.
    #:
    #: :type: :class:`str`
    #: :default: ``''``
    ftn = TypedField(str)

    #: The CUDA compiler to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the compiler defined in the current programming environment will be
    #: used.
    #:
    #: :type: :class:`str`
    #: :default: ``''``
    nvcc = TypedField(str)

    #: The C compiler flags to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the corresponding flags defined in the current programming environment
    #: will be used.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    cflags = TypedField(typ.List[str])

    #: The preprocessor flags to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the corresponding flags defined in the current programming environment
    #: will be used.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    cppflags = TypedField(typ.List[str])

    #: The C++ compiler flags to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the corresponding flags defined in the current programming environment
    #: will be used.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    cxxflags = TypedField(typ.List[str])

    #: The Fortran compiler flags to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the corresponding flags defined in the current programming environment
    #: will be used.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    fflags  = TypedField(typ.List[str])

    #: The linker flags to be used.
    #: If empty and :attr:`flags_from_environ` is :class:`True`,
    #: the corresponding flags defined in the current programming environment
    #: will be used.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    ldflags = TypedField(typ.List[str])

    #: Set compiler and compiler flags from the current programming environment
    #: if not specified otherwise.
    #:
    #: :type: :class:`bool`
    #: :default: :class:`True`
    flags_from_environ = TypedField(bool)

    def __init__(self):
        self.cc  = ''
        self.cxx = ''
        self.ftn = ''
        self.nvcc = ''
        self.cflags = []
        self.cxxflags = []
        self.cppflags = []
        self.fflags  = []
        self.ldflags = []
        self.flags_from_environ = True

    @abc.abstractmethod
    def emit_build_commands(self, environ):
        '''Return the list of commands for building using this build system.

        The build commands, as well as this function, will always be executed
        from the test's stage directory.

        :arg environ: The programming environment for which to emit the build
           instructions.
           The framework passes here the current programming environment.
        :type environ: :class:`reframe.core.environments.ProgEnvironment`
        :raises: :class:`BuildSystemError` in case of errors when generating
          the build instructions.

        .. versionchanged:: 3.5.0
           This function executes from the test stage directory.

        :meta private:

        '''

    def post_build(self, buildjob):
        '''
        houchuli
        Callback function that the framework will call when the compilation
        is done.

        Build systems may use this information to do some post processing and
        provide additional, build system-specific, functionality to the users.

        This function will always be executed from the test's stage directory.

        .. versionadded:: 3.5.0
        .. versionchanged:: 3.5.2
           The function is executed from the stage directory.

        :meta private:

        '''

    def _resolve_flags(self, flags, environ):
        _flags = getattr(self, flags)
        if _flags:
            return _flags

        if self.flags_from_environ:
            return getattr(environ, flags)

        return None

    def _cc(self, environ):
        return self._resolve_flags('cc', environ)

    def _cxx(self, environ):
        return self._resolve_flags('cxx', environ)

    def _ftn(self, environ):
        return self._resolve_flags('ftn', environ)

    def _nvcc(self, environ):
        return self._resolve_flags('nvcc', environ)

    def _cppflags(self, environ):
        return self._resolve_flags('cppflags', environ)

    def _cflags(self, environ):
        return self._resolve_flags('cflags', environ)

    def _cxxflags(self, environ):
        return self._resolve_flags('cxxflags', environ)

    def _fflags(self, environ):
        return self._resolve_flags('fflags', environ)

    def _ldflags(self, environ):
        return self._resolve_flags('ldflags', environ)

    def __str__(self):
        return type(self).__name__

    def __rfm_json_encode__(self):
        return str(self)
    
class EasyBuild(BuildSystem):
    '''A build system for building test code using `EasyBuild
    <https://easybuild.io/>`__.

    ReFrame will use EasyBuild to build and install the code in the test's
    stage directory by default. ReFrame uses environment variables to
    configure EasyBuild for running, so Users can pass additional options to
    the ``eb`` command and modify the default behaviour.

    .. versionadded:: 3.5.0

    '''

    #: The list of easyconfig files to build and install.
    #: This field is required.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    easyconfigs = TypedField(typ.List[str])

    #: Options to pass to the ``eb`` command.
    #:
    #: :type: :class:`List[str]`
    #: :default: ``[]``
    options = TypedField(typ.List[str])

    #: Instruct EasyBuild to emit a package for the built software.
    #: This will essentially pass the ``--package`` option to ``eb``.
    #:
    #: :type: :class:`bool`
    #: :default: ``[]``
    emit_package = TypedField(bool)

    #: Options controlling the package creation from EasyBuild.
    #: For each key/value pair of this dictionary, ReFrame will pass
    #: ``--package-{key}={val}`` to the EasyBuild invocation.
    #:
    #: :type: :class:`Dict[str, str]`
    #: :default: ``{}``
    package_opts = TypedField(typ.Dict[str, str])

    #: Default prefix for the EasyBuild installation.
    #:
    #: Relative paths will be appended to the stage directory of the test.
    #: ReFrame will set the following environment variables before running
    #: EasyBuild.
    #:
    #: .. code-block:: bash
    #:
    #:    export EASYBUILD_BUILDPATH={prefix}/build
    #:    export EASYBUILD_INSTALLPATH={prefix}
    #:    export EASYBUILD_PREFIX={prefix}
    #:    export EASYBUILD_SOURCEPATH={prefix}
    #:
    #: Users can change these defaults by passing specific options to the
    #: ``eb`` command.
    #:
    #: :type: :class:`str`
    #: :default: ``easybuild``

    '''
    environ: 
        options:
            -Dr /lr/--try-toolchain...
        easyconfigs:
            [a.eb,b.eb,c.eb....]
        installpath(prefix):
            default-prefix or prefix

    '''
    prefix = TypedField(str)

    def __init__(self):
        super().__init__()
        self.easyconfigs = []
        self.options = []
        self.emit_package = False
        self.package_opts = {}
        self.prefix = 'easybuild'
        self._eb_modules = []

    def emit_build_commands(self,environ):
        if not self.easyconfigs:
            raise ValueError(f"'easyconfigs' must not be empty")

        easyconfigs = ' '.join(self.easyconfigs)
        if self.emit_package:
            self.options.append('--package')
            for key, val in self.package_opts.items():
                self.options.append(f'--package-{key}={val}')

        # prefix = os.path.join(os.getcwd(), self.prefix)
        prefix = "/gpfs/fuyun"
        options = ' '.join(self.options)
        return [f'export EASYBUILD_PREFIX={prefix} && eb {easyconfigs} {options}']
        # return [f'export EASYBUILD_BUILDPATH={prefix}/build',
        #         f'export EASYBUILD_INSTALLPATH={prefix}',
        #         f'export EASYBUILD_PREFIX={prefix}',
        #         f'export EASYBUILD_SOURCEPATH={prefix}',
        #         f'eb {easyconfigs} {options}']

    def post_build(self, buildjob):
        # Store the modules generated by EasyBuild

        modulesdir = os.path.join(os.getcwd(), self.prefix,
                                  'modules', 'all')
        with open(buildjob.stdout) as fp:
            out = fp.read()

        self._eb_modules = [
            {'name': m, 'collection': False, 'path': modulesdir}
            for m in re.findall(r'building and installing (\S+)...', out)
        ]

    @property
    def generated_modules(self):
        return self._eb_modules


def search_tmple_file(name,templefile,*args,**kwargs):
    """Find templefile match  packages  name (in /gpfs/fuyun/fy_modules and other  /gpfs/fuyun/fy_modules/gemray)."""
    templepath  = None
    flag = 1
    software_path = "/gpfs/fuyun/fy_modules/physics/" 
    templefilename = "temple.yaml"

    if Path(templefile).is_file() :
        # templepath = Path(tmplefile).parent
        return templefile
    elif  Path(Path(Path(software_path).joinpath(templefilename))).is_file() :
        print("helklo")
        search = Path(Path(Path(software_path).joinpath(name,templefilename)))
        print(search)
        return Path(Path(Path(software_path).joinpath(templefilename)))
    elif Path(Path(Path(software_path).joinpath(name,templefilename))).is_file() :
        search = Path(Path(Path(software_path).joinpath(name,templefilename)))
        print(search)
        return Path(Path(Path(software_path).joinpath(name,templefilename)))
    else:
        raise  RuntimeError('could fount the templefile ,please gime me it  ') 

def get_metadat(filename):
    name = "genray"
    templefile = filename
    filename = search_tmple_file(name,templefile)
    path = str(filename)
    print(path)
    test = ModuleRepository()
    test.load_configure(path)
    print(test._conf)
    license = test._conf.get("license")
    print(license)
    logger.debug(f"the default_tag name from the default-configure  is '{license}'")

def test_easybuild(environ, tmp_path,**kwargs):
    build_system = EasyBuild()
    build_system.easyconfigs = ['Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb']
    build_system.options = ['-Dr', '--try-toolchain-version=9.3.0',"--minimal-toolchains","--try-update-deps","--experimental"]
    chang_dir=change_dir(tmp_path)
    print(build_system.emit_build_commands(environ))
    with change_dir(tmp_path):
        print(tmp_path)
        print([
            f'export EASYBUILD_BUILDPATH={tmp_path}/easybuild/build',
            f'export EASYBUILD_INSTALLPATH={tmp_path}/easybuild',
            f'export EASYBUILD_PREFIX={tmp_path}/easybuild',
            f'export EASYBUILD_SOURCEPATH={tmp_path}/easybuild',
            'eb Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb  -Dr --try-toolchain-version=9.3.0 --minimal-toolchains --try-update-deps --experimental'
        ])
        assert build_system.emit_build_commands(environ) == [
            f'export EASYBUILD_BUILDPATH={tmp_path}/easybuild/build',
            f'export EASYBUILD_INSTALLPATH={tmp_path}/easybuild',
            f'export EASYBUILD_PREFIX={tmp_path}/easybuild',
            f'export EASYBUILD_SOURCEPATH={tmp_path}/easybuild',
            'eb Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb -Dr --try-toolchain-version=9.3.0 --minimal-toolchains --try-update-deps --experimental'
        ]
    # easybuild_cmd = build_system.emit_build_commands(environ)
    easybuild_cmd = 'eb Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb -Dr --try-toolchain-version=9.3.0 --minimal-toolchains --try-update-deps --experimental'
    test= Module(**kwargs)
    out= test._run_command(easybuild_cmd)
    print(out)
    










