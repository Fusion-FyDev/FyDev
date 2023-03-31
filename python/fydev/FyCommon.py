import os

FY_ROOT = os.environ.get("FY_ROOT", '~/.fydev')
FY_INSTALL_DIR = os.environ.get("FY_INSTALL_DIR", f"{FY_ROOT}/software")
FY_SOURCE_DIR = os.environ.get("FY_SOURCE_DIR", f"{FY_ROOT}/source")
FY_BUILD_DIR = os.environ.get("FY_BUILD_DIR", f"{FY_ROOT}/build")
FY_REPOSITORY_DIR = os.environ.get("FY_REPOSITORY_DIR", f"{FY_ROOT}/repository")

# module from SpDM
