import codecs
import json
import sys

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


if __name__ == "__main__":
    parse_file = sys.argv[1]
    candidates_file_out = sys.argv[2]

    export_discourse_relations_candidates_to_file(parse_file, candidates_file_out)





