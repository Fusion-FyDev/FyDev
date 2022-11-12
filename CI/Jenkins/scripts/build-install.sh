#!/bin/bash
ls -lh /fuyun
su  fydev  -c ' whoami  && 
source /usr/share/lmod/lmod/init/bash && 
module load EasyBuild/4.2.0 && 
echo $MODULEPATH &&
echo "hello world" &&
# export MODULEPATH=~/.local/easybuild/modules/all/:$MODULEPATH &&
eb -Dr  --filter-deps=OpenMPI,netCDF --robot-paths=./easybuild/easyconfigs:/fuyun/software/EasyBuild/4.2.0/easybuild/easyconfigs  ${FY_MODULENAME}.eb  &&
eb -lr --rebuild  --filter-deps=OpenMPI,netCDF  --robot-paths=./easybuild/easyconfigs:/fuyun/software/EasyBuild/4.2.0/easybuild/easyconfigs ${FY_MODULENAME}.eb '
