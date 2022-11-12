---
title: HPC 环境中复杂科学软件包管理和持续集成系统
subtitle: FyDev 用户使用手册
Author: 刘晓娟，xiaojuan.liu@ipp.ac.cn
toc-title: 目录
number-section: True
mainfont: Noto Sans Mono CJK SC
---


## 引言

### 标识

- 软件名称：HPC 环境中复杂科学软件包管理和持续集成系统
- 版本号：v0.1
- 完成时间：2021.8.26

### 系统概述

FyDEV 是一套 HPC 环境中复杂科学软件包管理和持续集成系统，通过一系列“模块描述”文件描述整个软件仓库的状态，并纳入版本管理系统。将对复杂软件仓库的管理转化为对模块描述文件的管理；同时结合持续集成的思想，动态追踪记录科学软件的构建过程，进而实现对整个软件仓库的自动化管理和溯源信息记录。该系统为整个集成建模平台提供了统一的包管理运行环境，同时对软件包构建过程的溯源信息记录弥补了传统数据结果元数据中对模块运行环境记录的缺失，对未来整个集成建模系统内结果数据的可追溯性研究具有重要意义。

**FyDEV**是由中国科学院等离子体物理研究所开发。主要贡献人员包括：

- 框架设计：于治，yuzhi@ipp.ac.cn
- 代码编写：刘晓娟，xiaojuan.liu@ipp.ac.cn
- 文档管理：刘晓娟，xiaojuan.liu@ipp.ac.cn

本程序开发受到下列项目支持：

- 国家磁约束核聚变能发展研究专项（National MCF Energy R&D Program under Contract），氘氚聚变等离子体中 alpha 粒子过程对等离子体约束 性能影响的理论模拟研究，Alpha 粒子密度和能谱分布的集成建模研究，编号 2018YFE0304102
- 聚变堆主机关键系统综合研究设施 （ Comprehensive Research Facility for Fusion Technology Program of China）总控系统， 集成数值建模和数据分析系统框架开发，编号 No. 2018-000052-73-01-001228.

### 文档概述

本文档为 FyDEV 的《使用说明》。

## 软件综述

### 软件应用

FyDEV 包含一系列配置文件和 python 源码“模块”文件；

- 源码文件主要是对模块构建过程中需要的功能，主要包括模块的检查、解析依赖、模块列出、安装、部署等一系列。
- 配置文件主要包含整个系统运行所需的依赖环境：
  - 包含 HPC 上包管理软件 EasyBuild 的部署，及基本的工具链环境的建立方法；
  - 软件仓库 Gitlab 的服务的部署；
  - 持续集成平台的基本环境 GitLab-CI/Jenkins 的部署、运行所需的脚本
  - 建立容器化的 pipeline 运行环境所需的 Dockerfile、docker-compose 等文件

### 软件清单

```files
./CI
|-- Gitlab-CI
|   |-- DockerFile
|   |   `-- docker-compose.yml
|   `-- scripts
|       |-- checkpa.py
|       |-- ci-build.py
|       |-- ci-dependlist.py
|       |-- ci-deploy.py
|       |-- ci-ebfilescheck.py
|       |-- ci-fetchsources.py
|       |-- deal_yamlfile.py
|       |-- init-StandardModule.py
`-- Jenkins
    |-- DockerFile
    |   |-- docker-compose.yml
    |   |-- dockerfile
    |   |-- jenkinsfile
    |   |-- jenkins_plugin_url
    |   |-- load-jenkins-blueocean.sh
    |   |-- plugins.txt
    |   `-- README.md
    |-- Jenkinsfile
    `-- scripts
        |-- build-install.sh
        |-- check_eb.sh
        |-- check_initiallzation.sh
        |-- check_modulefile_exit.sh
        |-- deploy.sh
        |-- file_exit.py
        |-- fy_deploy.py
        |-- load-python.sh
        |-- modulefile_exit.py
        |-- replace_value.py
./docs
|-- source_code_1.md
`-- UserManual.md
./EbfilesRespository
|-- genray-mpi-201213-gompi-2019b.eb
|-- genray-mpi-201213-gompi-2020a.eb
`-- pgplot-5.2-GCCcore-9.3.0.eb
./ModuleRepository
|-- genray
|   `-- temple.yaml
|-- genray-mpi
    |-- genray-mpi.yaml
    `-- temple.yaml
./python
|-- fypm
|   |-- EasyBuildPa.py
|   |-- __init__.py
|   |-- ModuleEb.py
|   |-- ModulePa.py
|   |-- StandardModule.py
|-- readme.md
`-- requirements.txt
./runner
`-- DockerFile
```

### 软件环境

- 硬件环境：X86 兼容架构平台环境

- 语言环境：

  - Python >= 3.8
  - Bash Shell

- 依赖：

  - EasyBuild

## 使用软件指南

### 系统构架

![image-20210902143041323](../picture/devops-pipeline-1.jpg)

FyDEV 主要涉及以下几个部分：

- 包含已部署了 EasyBuil 的 HPC 运行环境：最终面像用户的生产环境。
- 基于 GitLab 的软件仓库和 Gitlab-CI 的构建环境：提供仓库管理平台，和持续集成运行环境。
- 运行在 Gitlab-runner 上的持续集成 pipeline：支持物理节点、虚拟节点、容器化节点的 runner，灵活支持 pipeline 运行过程。

### 使用方法

- 单个物理模块操作

  ```python
  from fypm.ModuleEb import ModuleEb
  configure_path ="/gpfs/fuyun/software/FyBuild/python/tests/data//FuYun/configure.yaml"
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

    ![image-20210902121750746](../picture/cmake-install.png)

  - 部署模块

    ```python
    module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
    module.deploy()
    ```

- 自动化构建物理模块

  ```python
  from fypm.ModuleEb import ModuleEb
  configure_path ="/gpfs/fuyun/software/FyBuild/python/tests/data//FuYun/configure.yaml"
  >>>python trigger.py
  ```

  ![image-20210902121743428](../picture/pipeline-all.png)
