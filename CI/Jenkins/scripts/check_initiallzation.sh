#!/bin/bash
# KEYWORDS="CHECK BUILD REBUILD TEST DEPLOY"
# KEYWORD="CHECK"
if [[ ${KEYWORDS} =~ ${KEYWORD} ]]
then
    flag=1
    # echo "currentBuild.result = "ABORTED"  "
else
    flag=0
    # echo "currentBuild.result = "SUCCESS" "
fi
echo $flag
# echo "KEYWORD=${KEYWORDS}"
# echo "KEYWORD=${KEYWORD}"
# echo "currentBuild.result=${currentBuild.result}"
# echo "the test of initiallzation is finish"