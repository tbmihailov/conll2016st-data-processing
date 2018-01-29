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

coreNlpPath="/home/mitarb/mihaylov/research/TAC2016/tac2016-kbp-event-nuggets/corenlp/stanford-corenlp-full-2015-12-09/*;"

files_cnt=1
for ((i=0;i<files_cnt;i++)); do
    echo "---------------"
    input_dir=${input_dirs[${i}]}
    output_dir=${output_dirs[${i}]}

    echo "input_dir: ${input_dir}"
    echo "output_dir: ${output_dir}"

    python data/AIPHESSummarizaiton/raw_text_to_json.py ${input_dir} ${output_dir} ${coreNlpPath}

    echo "---------------"
done