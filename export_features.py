import json
import sys

import os

def get_doc_int_id_from_text_id(doc_id_txt):
    index = doc_id_txt.index(":doc_") + len(":doc_")
    id_int = int(doc_id_txt[index:])

    return id_int


if __name__ == "__main__":
    print get_doc_int_id_from_text_id("d30003t-input.txt:doc_7")

    # input dir
    input_dir = sys.argv[1]
    input_dir = os.path.abspath(input_dir)

    # output dir
    output_dir = sys.argv[2]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print "%s created" % output_dir
    output_dir = os.path.abspath(output_dir)


    features = {}
    discourse_relations_file = "output.json"

    files_to_export = []

    def get_feature_id(feature_text):
        if feature_text in features:
            feat_info = features[feature_text]
            feat_info["cnt"] += 1
            return feat_info["id"]
        else:
            feat_info = {"id": len(features), "cnt": 1}
            features[feature_text] = feat_info
            return feat_info["id"]

    for dirpath, dirnames, files in os.walk(input_dir):
        for name in files:
            if name.lower().endswith(discourse_relations_file):
                if dirpath.endswith("_prep"):
                    files_to_export.append({"dir_path": dirpath,
                                            "out_dir": os.path.abspath(os.path.join(dirpath, os.pardir)).replace(input_dir, output_dir),
                                            "out_feats_file": dirpath.replace(input_dir, output_dir).replace("_prep", "")})

    print "Files to export: %s" % len(files_to_export)
    for export_info in files_to_export:
        # document structure
        docs_with_sent_features = []
        parses_raw = json.load(open(os.path.join(export_info["dir_path"], "parses_raw.json")))

        keys_ordered = sorted(parses_raw.keys(), key=lambda k: get_doc_int_id_from_text_id(k))

        for key in keys_ordered:
            doc = parses_raw[key]
            doc_feats = {"ID": doc["ID"],
                         "ID_int": get_doc_int_id_from_text_id(doc["ID"]),
                         "line_start": doc["line_start"],
                         "sentences": [[] for x in range(len(doc["sentences_text"]))]}

            assert doc_feats["ID_int"] == len(docs_with_sent_features), "Documents not ordered!"
            docs_with_sent_features.append(doc_feats)
        #del parses_raw

        # export the actual features
        #DR output
        dr_output_file = os.path.join(export_info["dir_path"], "output.json")
        for line in open(dr_output_file):
            dr_instance_json = json.loads(line)
            curr_doc_id = get_doc_int_id_from_text_id(dr_instance_json["DocID"])

            sent_id_arg1 = dr_instance_json["Arg1"]["TokenList_full"][0][3] if len(dr_instance_json["Arg1"]["TokenList_full"])>0 else -1
            sent_id_arg2 = dr_instance_json["Arg2"]["TokenList_full"][0][3] if len(dr_instance_json["Arg2"]["TokenList_full"])>0 else -1
            sent_id_conn = dr_instance_json["Connective"]["TokenList_full"][0][3] if len(dr_instance_json["Connective"]["TokenList_full"])>0 else -1

            # print (sent_id_arg1, sent_id_arg2, sent_id_conn, curr_doc_id)
            # print len(docs_with_sent_features[curr_doc_id]["sentences"])


            feat_dr_type = "DR_Sense_%s_%s" % (dr_instance_json["Type"][:3], dr_instance_json["Sense"][0])
            if dr_instance_json["Type"] == "Explicit":
                if sent_id_arg1 >= 0:
                    docs_with_sent_features[curr_doc_id]["sentences"][sent_id_arg1].append(get_feature_id(feat_dr_type))
                else:
                    docs_with_sent_features[curr_doc_id]["sentences"][sent_id_arg2].append(get_feature_id(feat_dr_type))
            else:
                if sent_id_arg1 >= 0:
                    docs_with_sent_features[curr_doc_id]["sentences"][sent_id_arg1].append(get_feature_id(feat_dr_type+"_Arg1"))
                if sent_id_arg2 >= 0:
                    docs_with_sent_features[curr_doc_id]["sentences"][sent_id_arg2].append(get_feature_id(feat_dr_type+"_Arg2"))

            if len(dr_instance_json["Connective"]["RawText"]) > 0:
                docs_with_sent_features[curr_doc_id]["sentences"][sent_id_conn].append(
                    get_feature_id("DR_Conn_"+dr_instance_json["Connective"]["RawText"].replace(" ", "_")))
                docs_with_sent_features[curr_doc_id]["sentences"][sent_id_conn].append(get_feature_id(
                    "DR_SenseConn_%s_%s_%s" % (dr_instance_json["Type"][:3], dr_instance_json["Sense"][0], dr_instance_json["Connective"]["RawText"].replace(" ", "_"))))

        # export file features
        exp_delim_feat = " "
        exp_delim_line = "\n"

        print "Out features file:%s" % export_info["out_feats_file"]
        if not os.path.exists(export_info["out_dir"]):
            os.makedirs(export_info["out_dir"])
            print "%s created" % export_info["out_dir"]

        f_exp = open(export_info["out_feats_file"], "w")
        for di, doc in enumerate(docs_with_sent_features):
            for si, sent in enumerate(doc["sentences"]):
                for fi in range(len(sent)):
                    f_exp.write(str(sent[fi]))
                    if fi < (len(sent) - 1):
                        f_exp.write(exp_delim_feat)
                f_exp.write(exp_delim_line)
            if di < (len(docs_with_sent_features)-1):
                f_exp.write(exp_delim_line)

    # Vocabulary export
    feats_sorted = sorted([(feat_info["id"], feat_name, feat_info["cnt"]) for feat_name, feat_info in features.iteritems()], key=lambda a:a[0])
    out_file_vocab = os.path.join(output_dir, "input.txt")
    print "Exporting vocabulary: %s" % out_file_vocab
    f_exp_vocab = open(out_file_vocab, "w")
    for feat in feats_sorted:
        f_exp_vocab.write("%s\t%s" % (feat[0], feat[1]))
    f_exp_vocab.close()

    # by frequency
    feats_sorted = sorted(feats_sorted, key=lambda a: a[2], reverse=True)
    out_file_vocab = os.path.join(output_dir, "input_freq.txt")
    f_exp_vocab = open(out_file_vocab, "w")
    for feat in feats_sorted:
        f_exp_vocab.write("%s\t%s\t%s\n" % (feat[0], feat[1], feat[2]))
    f_exp_vocab.close()












