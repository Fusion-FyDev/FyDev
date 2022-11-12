#### FyBuild
--------------------------------------------------------------------------------
As described, FyDev is a management framework for scientific software computing environments, enabling the management of software environments and the build process following the FAIR principles.
FyBuild is a submodule of the FyDev project. It parses its build process based on existing module description files or module configuration files. The FyBuild tool increases the accessibility of scientific software and the interoperability of multiple dependent software environments during the build process.

#### Dependency Environment

- Hardware environment:
    - X86 compatible architecture platform environment

- Language Environment: Python

    - Python >= 3.8
    - Bash Shell

- Dependent tools: EasyBuild

    - EasyBuild
#### method example
- Step-by-step construction of research software

  ```python
  from fypm.ModuleEb import ModuleEb
  configure_path ="./data//FuYun/configure.yaml"
  ```

  - Check for the existing

    ```python
    module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.checkpa()
    ```

  - List relevant software which is installed

    ```python
    module = ModuleEb(name='genray-mpi',version='',tag=" ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    modulelist=module.list_avail_pa()
    >>>print(modulelist)
    ['genray-mpi/200118-gompi-2019b', 'genray-mpi/201213-gompi-2019b', 'genray-mpi/201213-gompi-2020a']
    ```

  - get sources

    ```python
    module = ModuleEb(name='zlib',version='1.2.11',tag="GCCcore-9.3.0 ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    ebsources=module.fetch_sources(dry_run=True)
    >>>print(ebsources.src)
    [{'name': 'zlib-1.2.11.tar.gz', 'path': '/gpfs/fuyun/sources/z/zlib/zlib-1.2.11.tar.gz', 'cmd': None, 'checksum': 'c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1', 'finalpath': '/gpfs/fuyun/build/zlib/1.2.11/GCCcore-9.3.0'}]

    ```

  - install 

    ```python
    module = ModuleEb(name='CMake',version='3.16.5',tag="GCCcore-9.3.0 ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.build_install(args=['--rebuild', '--minimal-toolchains']，, silent=True)
    ```


  - deploy

    ```python
    module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.deploy()
    ```

- Automating the building of research software based on CI/CD

  ```python
  from fypm.ModuleEb import ModuleEb
  configure_path ="./data//FuYun/configure.yaml"
  >>>python ./tests/ModuleEb-test/trigger.py
  ```
