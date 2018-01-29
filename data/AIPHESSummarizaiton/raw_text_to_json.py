import codecs
import json
import sys

import errno
import os
import traceback

from stanford_corenlp_pywrapper import CoreNLP

from data.AIPHESSummarizaiton.generate_candidates_from_parses import export_discourse_relations_candidates_to_file
from data.AIPHESSummarizaiton.raw_json_to_conll2016_json import convert_raw_json_to_conll2016_json


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def get_file_base_name(file_path):
    base_name = os.path.basename(file_path)  # filename with extension
    #name_split = os.path.splitext(base_name)

    return base_name

def save_data_to_json_file(data, output_json_file):
    data_file = codecs.open(output_json_file, mode='wb', encoding="utf-8")
    json.dump(data, data_file)
    data_file.close()

def convert_raw_text_to_json_corenlp(input_dir, file_base_name):
    docs = {}
    doc_id = "%s:doc_%s" % (file_base_name, len(docs))
    curr_doc = {"ID": doc_id, "sentences_text": [], "sentences": [], "line_start": 0}

    file_name_full = os.path.join(input_dir, file_name)
    line_id = -1
    for line in codecs.open(file_name_full, 'rb'):
        line_id += 1
        line = line.strip()
        print ("Line %s, doc %s" % (line_id, doc_id))
        if line == "":
            # Document separator
            if doc_id not in docs and len(curr_doc["sentences_text"]) > 0:
                docs[doc_id] = curr_doc

            doc_id = "%s:doc_%s" % (file_base_name, len(docs))
            curr_doc = {"ID": doc_id, "sentences_text": [], "sentences": [], "line_start": line_id}

            continue

        curr_doc["sentences_text"].append(line)

        line_parse = parser.parse_doc(line)

        line_parse_single_sentence = line_parse["sentences"][0]
        if len(line_parse["sentences"]) > 1:
            print("Warning - multiple sentences (%s) at line %s in file %s" % (
            len(line_parse["sentences"]), line_id, file_name_full))
        curr_doc["sentences"].append(line_parse_single_sentence)

    if doc_id not in docs and len(curr_doc["sentences_text"]) > 0:
        docs[doc_id] = curr_doc

    return docs


if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    # read the files
    from os import listdir
    from os.path import isfile, join
    input_files_in_dir = [f for f in listdir(input_dir) if isfile(join(input_dir, f)) and f.endswith(".txt")]

    # CoreNLP
    # coreNlpPath="/home/mihaylov/research/TAC2016/tac2016-kbp-event-nuggets/corenlp/stanford-corenlp-full-2015-12-09/*;/home/mihaylov/research/TAC2016/tac2016-kbp-event-nuggets/corenlp/stanford-srparser-2014-10-23-models.jar"
    # #coreNlpPath="/home/mihaylov/research/TAC2016/tac2016-kbp-event-nuggets/corenlp/stanford-corenlp-full-2015-12-09/*;"
    #
    # # #server
    # # coreNlpPath="/home/mitarb/mihaylov/research/TAC2016/tac2016-kbp-event-nuggets/corenlp/stanford-corenlp-full-2015-12-09/*"
    # # coreNlpPath="/home/mitarb/mihaylov/research/TAC2016/tac2016-kbp-event-nuggets/corenlp/stanford-corenlp-full-2015-12-09/*;"

    coreNlpPath = "/Users/mihaylov/research/libs/corenlp_executables/stanford-corenlp-full-2015-12-09/*"
    if len(sys.argv) > 3:
        coreNlpPath = sys.argv[3]

    print "coreNlpPath:%s" % coreNlpPath

    parse_mode = "pos"  # "pos", "parse"
    parser = CoreNLP(parse_mode, corenlp_jars=coreNlpPath.split(';'))

    print("Processing %s input files.." % len(input_files_in_dir))
    for fid, file_name in enumerate(input_files_in_dir):
        print "-" * 10
        print "--- "+ file_name + " ---"
        print "-" * 10
        try:
            file_base_name = get_file_base_name(file_name)
            print("File %s of %s:%s" %(fid+1, len(input_files_in_dir), file_name))
            output_dir_file = os.path.join(output_dir, file_base_name+"_prep")

            if not os.path.exists(output_dir_file):
                os.makedirs(output_dir_file)

            file_parse_json = {}

            docs = convert_raw_text_to_json_corenlp(input_dir, file_base_name)

            # export the raw stanford corenlp

            current_file_parse_file = os.path.join(output_dir_file, "parses_raw.json")
            save_data_to_json_file(docs, current_file_parse_file)
            print("Saved file %s" % current_file_parse_file)

            print("Generating parses.json")
            # convert to conll2016st discourse rel json
            current_file_parse_conll = os.path.join(output_dir_file, "parses.json")
            docs_converted = convert_raw_json_to_conll2016_json(docs)
            save_data_to_json_file(docs_converted, current_file_parse_conll)

            print("Generating relations_no_sense.json")
            # convert to conll2016st discourse rel json
            current_file_candidates_file = os.path.join(output_dir_file, "relations-no-senses.json")
            export_discourse_relations_candidates_to_file(current_file_parse_file, current_file_candidates_file)


            print("Saved file %s" % current_file_parse_conll)
        except Exception as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print "Exception type:"
            print exc_type
            print "Exception value:"
            print exc_value
            traceback.print_exc()









