#!/bin/bash
ls -lh /gpfs/fuyun
su  fydev  -c ' whoami  && 
source /usr/share/lmod/lmod/init/bash && 
module use /gpfs/fuyun/modules/all &&
module load EasyBuild/4.2.0 && 
echo $MODULEPATH &&
echo "hello world" &&
# export MODULEPATH=~/.local/easybuild/modules/all/:$MODULEPATH &&
#add the building 文件在这里
export EASYBUILD_PREFIX=/gpfs/fuyun &&
eb --show-config &&
# module load genray-mpi/200118-gompi-2019b && 
# module show genray-mpi/200118-gompi-2019b &&
eb -Dr --filter-deps=OpenMPI,netCDF   --robot-paths=./easybuild/easyconfigs:/gpfs/fuyun/software/EasyBuild/4.2.0/easybuild/easyconfigs  ${FY_MODULENAME}  &&
eb -lr --rebuild --filter-deps=OpenMPI,netCDF --robot-paths=./easybuild/easyconfigs:/gpfs/fuyun/software/EasyBuild/4.2.0/easybuild/easyconfigs ${FY_MODULENAME} '
