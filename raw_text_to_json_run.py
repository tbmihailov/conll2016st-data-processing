import codecs
import json
import sys

import errno
import os
import traceback

from stanford_corenlp_pywrapper import CoreNLP

#from data.AIPHESSummarizaiton.generate_candidates_utils import export_discourse_relations_candidates_to_file
from data.common.DiscourseHelpers import DiscourseHelpers


def new_discourse_relation_item():
    new_item = {
        "DocID": "doc",
        "ID": None,
        "Sense": [],
        "Type": "Implicit", # "Explicit"
        "Arg1": {"CharacterSpanList": [],
                       "RawText": "",
                       "TokenList": []},
        "Connective": {"CharacterSpanList": [],
                   "RawText": "",
                   "TokenList": []},
        "Arg2": {"CharacterSpanList": [],
                       "RawText": "",
                       "TokenList": []},
    }

    return new_item

def create_explicit(doc_data, sent_id, conn_token_span, new_id):
    doc_id = doc_data["ID"]
    sent_text = doc_data["sentences_text"][sent_id]
    sent_parse = doc_data["sentences"][sent_id]

    new_item = new_discourse_relation_item()
    new_item["Type"] = "Explicit"
    new_item["DocID"] = doc_id
    new_item["ID"] = new_id

    new_item["Arg1"]["TokenList"] = [[0, 0, doc_data["line_start"] + sent_id, sent_id,x] for x in range(0, conn_token_span[0])]
    new_item["Arg1"]["CharacterSpanList"] = [0, sent_parse["char_offsets"][conn_token_span[0] - 1][1]]
    new_item["Arg1"]["RawText"] = sent_text[new_item["Arg1"]["CharacterSpanList"][0]:new_item["Arg1"]["CharacterSpanList"][1]]

    new_item["Connective"]["TokenList"] = [[0, 0, doc_data["line_start"] + sent_id, sent_id, x] for x in range(conn_token_span[0], conn_token_span[1])]
    new_item["Connective"]["CharacterSpanList"] = [sent_parse["char_offsets"][conn_token_span[0]][0], sent_parse["char_offsets"][conn_token_span[1] - 1][1]]
    new_item["Connective"]["RawText"] = sent_text[new_item["Connective"]["CharacterSpanList"][0]:new_item["Connective"]["CharacterSpanList"][1]]

    new_item["Arg2"]["TokenList"] = [[0, 0, doc_data["line_start"] + sent_id, sent_id, x] for x in range(conn_token_span[1], len(sent_parse["char_offsets"]))]
    new_item["Arg2"]["CharacterSpanList"] = [sent_parse["char_offsets"][conn_token_span[1]][1], sent_parse["char_offsets"][-1][1]]
    new_item["Arg2"]["RawText"] = sent_text[new_item["Arg2"]["CharacterSpanList"][0]:new_item["Arg2"]["CharacterSpanList"][1]]

    return new_item

def create_implicit(doc_data, sent1_id, sent2_id, cand_id):
    new_item = new_discourse_relation_item()
    new_item["Type"] = "Implicit"
    new_item["DocID"] = doc_data["ID"]
    new_item["ID"] = cand_id

    new_item["Arg1"]["TokenList"] = [[0, 0, doc_data["line_start"] + sent1_id, sent1_id, x] for x in range(0, len(doc_data["sentences"][sent1_id]["tokens"]))]
    new_item["Arg1"]["RawText"] = doc_data["sentences_text"][sent1_id]

    new_item["Arg2"]["TokenList"] = [[0, 0, doc_data["line_start"] + sent2_id, sent2_id, x] for x in range(0, len(doc_data["sentences"][sent2_id]["tokens"]))]
    new_item["Arg2"]["RawText"] = doc_data["sentences_text"][sent2_id]

    return new_item

def export_discourse_relations_candidates_to_file(parse_file, candidates_file_out):
    f = codecs.open(parse_file, "rb")
    parses_json = json.load(f)

    connectives_to_check = DiscourseHelpers.CONNECTIVES_SORTED

    candidates_list = []
    cand_id = 0
    for doc_id_key, doc_data in parses_json.iteritems():
        for sent_id, sent in enumerate(doc_data["sentences_text"]):
            sent_parse = doc_data["sentences"][sent_id]

            # explicit connectives
            for connective in connectives_to_check:
                if connective in sent:
                    curr_conn_start = sent.find(connective)  # sent.indexof(connective)
                    curr_conn_end = curr_conn_start + len(connective)

                    # print "%s" % (sent[curr_conn_start - 1:curr_conn_end+1].replace(" ", "_"))
                    if (curr_conn_end >= len(sent) or sent[curr_conn_end] not in [" ", ",", "-"]) \
                            or curr_conn_start - 1 < 0 or sent[curr_conn_start - 1] not in [" ", ",", "-"]:
                        # eliminate matches that are contained in a word
                        curr_conn_start = -1
                        curr_conn_end = -1
                        # print "skip"
                        continue

                    if curr_conn_start > 0:
                        conn_tokens_start = -1
                        conn_tokens_end = -1

                        for tkn_id, char_offset in enumerate(sent_parse["char_offsets"]):
                            if conn_tokens_start == -1:
                                if curr_conn_start >= char_offset[0] and curr_conn_start <= char_offset[1]:
                                    conn_tokens_start = tkn_id
                                    if curr_conn_end >= char_offset[0] and curr_conn_end <= char_offset[1]:
                                        conn_tokens_end = tkn_id + 1
                                        break
                            elif conn_tokens_end == -1:
                                if curr_conn_end >= char_offset[0] and curr_conn_end <= char_offset[1]:
                                    conn_tokens_end = tkn_id + 1
                                    break

                        cand_id += 1
                        new_candidate_explicit = create_explicit(doc_data, sent_id,
                                                                 [conn_tokens_start, conn_tokens_end], cand_id)
                        candidates_list.append(new_candidate_explicit)

            # explicit connectives
            if sent_id > 0:
                cand_id += 1
                new_candidate_implicit = create_implicit(doc_data, sent_id - 1, sent_id, cand_id)
                candidates_list.append(new_candidate_implicit)

    # export candidates
    file = codecs.open(candidates_file_out, "wb")
    for candidate in candidates_list:
        file.write(json.dumps(candidate))
        file.write("\n")
    print ("Exported %s candidates to %s" % (len(candidates_list), candidates_file_out))

#from data.AIPHESSummarizaiton.raw_json_to_conll2016_json import convert_raw_json_to_conll2016_json


def convert_raw_json_to_conll2016_json(raw_json):
    docs_converted = {}
    for doc_id_key, doc_data in raw_json.iteritems():
        curr_doc = {}
        curr_doc["ID"] = doc_data["ID"]
        curr_doc["line_start"] = doc_data["line_start"]
        curr_doc["sentences"] = []
        for sent in doc_data["sentences"]:
            words_converted = [[t, {"PartOfSpeech": sent["pos"][tid]}] for tid, t in enumerate(sent["tokens"])]
            sent_new = {"words": words_converted}
            curr_doc["sentences"].append(sent_new)

        docs_converted[doc_id_key] = curr_doc

    return docs_converted

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









