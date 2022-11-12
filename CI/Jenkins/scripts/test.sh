#!bin/bash
mes="module spider cql3d "
(module spider cql3d) 2>result.log
mes1="Lmod has detected the following error:  Unable to find: "cql3d"."
if [[ `$mes` == $mes1 ]] 
then 
    echo "ok" 
else 
    echo `$mes`
    echo "no ok" 
fi
strA="helloworld"
strB="low"
if [[ $strA =~ $strB ]]
then
  echo "包含"
else
  echo "不包含"
fi
