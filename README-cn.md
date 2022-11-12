### FyBuild

正如描述的那样，FyDev是一个科学软件计算环境的管理框架，使得对软件环境管理和构建过程遵循FAIR原则。
FyBuild是FyDev项目中的一个子模块。它根据已有的模块描述文件或者模块配置文件来解析它的构建过程。进一步，根据被解析的步骤自动构建科学软件，并在软件栈中生成可执行文件。FyBuild工具可以增加科学软件的可访问性及多个依赖软件环境构建过程中的互操作性。

#### 依赖环境

- 硬件环境：X86 兼容架构平台环境

- 语言环境：

  - Python >= 3.8
  - Bash Shell

- 依赖工具：

  - EasyBuild

#### 使用方法
- 单个物理模块操作

  ```python
  from fypm.ModuleEb import ModuleEb
  configure_path ="./data//FuYun/configure.yaml"
  ```

  - 检查物理模块是否存在

    ```python
    module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.checkpa()
    ```

  - 列出已经存在的相关程序

    ```python
    module = ModuleEb(name='genray-mpi',version='',tag=" ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    modulelist=module.list_avail_pa()
    >>>print(modulelist)
    ['genray-mpi/200118-gompi-2019b', 'genray-mpi/201213-gompi-2019b', 'genray-mpi/201213-gompi-2020a']
    ```

  - 获取模块的源码

    ```python
    module = ModuleEb(name='zlib',version='1.2.11',tag="GCCcore-9.3.0 ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    ebsources=module.fetch_sources(dry_run=True)
    >>>print(ebsources.src)
    [{'name': 'zlib-1.2.11.tar.gz', 'path': '/gpfs/fuyun/sources/z/zlib/zlib-1.2.11.tar.gz', 'cmd': None, 'checksum': 'c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1', 'finalpath': '/gpfs/fuyun/build/zlib/1.2.11/GCCcore-9.3.0'}]

    ```

  - 安装模块

    ```python
    module = ModuleEb(name='CMake',version='3.16.5',tag="GCCcore-9.3.0 ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.build_install(args=['--rebuild', '--minimal-toolchains']，, silent=True)
    ```


  - 部署模块

    ```python
    module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.deploy()
    ```

- 自动化构建物理模块

  ```python
  from fypm.ModuleEb import ModuleEb
  configure_path ="./data//FuYun/configure.yaml"
  >>>python trigger.py
  ```
