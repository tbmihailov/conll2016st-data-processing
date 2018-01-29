#!/usr/bin/env bash

input_base_dir=/home/mitarb/mihaylov/research/data/aiphes-summarization-collab/test
input_dirs=(
${input_base_dir}/DUC2003
${input_base_dir}/DUC2004
${input_base_dir}/TAC2008A
${input_base_dir}/TAC2009A
${input_base_dir}/hMDS_A
${input_base_dir}/hMDS_M
${input_base_dir}/hMDS_V
)

output_base_dir=/home/mitarb/mihaylov/research/data/aiphes-summarization-collab/test_conll16st
output_dirs=(
${output_base_dir}/DUC2003
${output_base_dir}/DUC2004
${output_base_dir}/TAC2008A
${output_base_dir}/TAC2009A
${output_base_dir}/hMDS_A
${output_base_dir}/hMDS_M
${output_base_dir}/hMDS_V
)

coreNlpPath="/home/mitarb/mihaylov/research/libs/corenlp/stanford-corenlp-full-2015-12-09/*;"

files_cnt=7
for ((i=0;i<files_cnt;i++)); do
    echo "---------------"
    input_dir=${input_dirs[${i}]}
    output_dir=${output_dirs[${i}]}

    echo "input_dir: ${input_dir}"
    echo "output_dir: ${output_dir}"

    script_name=raw_text_to_json_run.py
    run_name=raw_text_to_json_run_${i}
    log_file=${input_dir}_convert_$(date +%y-%m-%d-%H-%M-%S).log
    . ~/tools/notify/script_started.sh

    echo " python raw_text_to_json_run.py ${input_dir} ${output_dir} ${coreNlpPath}"
    python raw_text_to_json_run.py ${input_dir} ${output_dir} ${coreNlpPath}  | tee -a ${log_file}

    . ~/tools/notify/script_stopped.sh

    echo "---------------"
done