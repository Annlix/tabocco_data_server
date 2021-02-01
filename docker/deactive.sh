#!/usr/bin/env bash
env_file='.docker-env'
tmp_env_file='.tmp-env'
if [ -e .tmp_env ]
then
    printf '' > ${tmp_env_file}
fi
while read line
do
    echo $line | sed "s/\([A-Z_]*\)=\([A-Za-z_0-9:.-]*\)/\1=''/" >> ${tmp_env_file}
done < ${env_file}
source ${tmp_env_file}
rm ${tmp_env_file}
