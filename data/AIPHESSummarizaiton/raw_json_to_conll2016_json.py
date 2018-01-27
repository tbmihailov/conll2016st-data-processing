import codecs
import json
import sys


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

        docs_converted[doc_id_key] = doc_data

    return docs_converted

if __name__ == "__main__":
    parse_file = sys.argv[1]

    f = codecs.open(parse_file, "rb")
    parses_json = json.load(f)

    docs_converted = convert_raw_json_to_conll2016_json(parses_json)









