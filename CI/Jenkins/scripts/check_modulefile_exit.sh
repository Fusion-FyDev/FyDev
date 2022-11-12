#!/bin/bash
echo "the name and version of module  is ${FY_MODULENAME} "
ls -lh ${DEPLOY_PATH} 
su  fydev  -c ' whoami  && 
# module use /fuyun/modules/all &&
source /usr/share/lmod/lmod/init/bash && 
module use ${DEPLOY_PATH}/modules/all
module load Python/3.7.4-GCCcore-8.3.0 && 
module list &&
echo "the name and version of module  is '+FY_MODULENAME+' " &&
# which python &&
flag=`python ./scripts/modulefile_exit.py '+FY_MODULENAME+' '+FY_MODULEVERSION+' ` &&
echo $flag '