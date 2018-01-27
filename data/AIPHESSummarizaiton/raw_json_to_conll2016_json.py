import codecs
import json
import sys

if __name__ == "__main__":
    parse_file = sys.argv[1]

    f = codecs.open(parse_file, "rb")
    parses_json = json.load(f)

    for doc_id_key, doc_data in parses_json.iteritems():
        doc_id_int = doc_data("ID")
        doc_start_line = doc_data("line_start")
