#!/bin/bash
ls -lh ${DEPLOY_PATH}
su  fydev  -c ' whoami  && 
# module use /fuyun/modules/all &&
source /usr/share/lmod/lmod/init/bash && 
module load Python/3.7.4-GCCcore-8.3.0 && 
module list &&
which python &&
echo "${COMMITMES}" &&
echo "${WORKSPACE}" &&
flag=`python ./scripts/file_exit.py ${WORKSPACE} ${COMMITMES}` &&
echo $flag '