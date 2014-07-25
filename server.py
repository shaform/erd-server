import argparse
import json
import os.path
import random
import sys

import db
import mention
import annotate

from flask import Flask, jsonify, request, Response

 
app = Flask(__name__)
 
stop_list = set()
with open('stop_list', 'r') as f:
    for l in f:
        ts = l.split(',')
        for t in ts:
            t = t.strip()
            stop_list.add(t)
            if len(t) > 1:
                stop_list.add(t[0].lower() + t[1:])

def stopped(text):
    if len(text) <= 1 or text in stop_list:
        return True
    elif len(text) <= 4 and text.isdigit():
        return True
    elif (text[0].lower() + text[1:]) in stop_list:
        return True
    return False

def second_id(mid):
    if mid is None:
        return 'None'
    else:
        return 'https://www.freebase.com' + mid

def filter_over(entities, report=False):
    entities.sort(key=lambda x: (x[0], x[1]))
    new_entities = []
    for e in entities:
        if len(new_entities) == 0 or e[0] >= new_entities[-1][1]:
            new_entities.append(e)
        else:
            if report:
                log_data('error', 'over-report', e, entities)
            if e[5] > new_entities[-1][5]:
                new_entities[-1] = e
    return new_entities

def filter_ft(entities, erd_db):
    return [e for e in entities if (e[4] in erd_db.erd_dict and e[2] in erd_db.erd_dict[e[4]])]

def merge_process(text, textID, allcase=False, topn=1,
        add=False, remove=False, more=False, reverse=False,
        both=0, ft=False,
        tagme=1, dbp=0.25, dbpc=0.3,
        **kwargs):
    dbp_entities, dbp_outs = dbpedia_process(text, textID, dbpc=dbpc, ft=ft)
    tg_entities, tg_outs = tagme_process(text, textID, ft=ft)
    grd_entities, _ = greedy_process(text, allcase, topn=topn)

    dbp_dict, dbp_out_dict = {}, {}
    for e in dbp_entities:
        dbp_dict[(e[0], e[1])] = e
    for e in dbp_outs:
        dbp_out_dict[(e[0], e[1])] = e

    entities = []
    for e in grd_entities:
        key = (e[0], e[1])
        if add and key in dbp_dict and dbp_dict[key][5] > dbp:
            entities.append(dbp_dict[key])
        elif not remove or key not in dbp_out_dict or dbp_out_dict[key][5] < dbp:
            entities.append(e)

    added = [(more, dbp_entities, dbp), (tagme != 1, tg_entities, tagme)]
    if reverse:
        added[0], added[1] = added[1], added[0]

    for doit, f_entities, score in added:
        if doit:
            non_over = []
            it = 0
            for e in f_entities:
                # skip all previous entries
                while it < len(entities) and entities[it][1] <= e[0]:
                    it += 1
                if it >= len(entities) or entities[it][0] >= e[1]:
                    non_over.append(e)

            for e in non_over:
                if e[5] > score:
                    entities.append(e)

            entities = filter_over(entities)

    both_list = []
    # both dbp
    if both % 2 == 1:
        both_list.append(dbp_entities)
    # both tg
    if (both // 2 ) % 2 == 1:
        both_list.append(tg_entities)

    for bl in both_list:
        new_entities = []
        allowed = set()
        for e in bl:
            allowed.add(e[2])
        for e in entities:
            if e[2] in allowed:
                new_entities.append(e)
        entities = filter_over(new_entities)

    return filter_over(entities), []

def tagme_process(text, textID, ft=False, **kwargs):
    entities = []
    out_entities = []
    ats, bts = tg_at.seperate_by_freebase(tg_at.raw_annotate(text, textID), erd_db)
    for at in ats:
        o = at['offset']
        if not stopped(at['text']):
            entities.append((o[0], o[1],
                at['mid'], second_id(at['mid']), at['text'], at['score'], 0.99))
    for bt in bts:
        o = bt['offset']
        out_entities.append((o[0], o[1],
            bt['mid'], second_id(bt['mid']), bt['text'], bt['score'], 0.99))
    if ft:
        entities = filter_ft(entities, erd_db)
    return filter_over(entities), out_entities

def dbpedia_process(text, textID, ft=False, dbpc=0.3, dbp=0.25, fdbp=False, **kwargs):
    entities = []
    out_entities = []
    ats, bts = db_at.seperate_by_freebase(db_at.raw_annotate(text, textID, dbpc=dbpc), erd_db)
    for at in ats:
        o = at['offset']
        if not stopped(at['text']):
            if fdbp and at['score'] < dbp:
                continue
            entities.append((o[0], o[1],
                at['mid'], second_id(at['mid']), at['text'], at['score'], at['popularity']))
    for bt in bts:
        o = bt['offset']
        out_entities.append((o[0], o[1],
            bt['mid'], second_id(bt['mid']), bt['text'], bt['score'], bt['popularity']))
    if ft:
        entities = filter_ft(entities, erd_db)
    return filter_over(entities, report=True), out_entities

def greedy_process(text, _, allcase=False, topn=1, **kwargs):
    entities = []
    mentions = mention.greedy_detector(erd_db, text, allcase=allcase)
    for m in mentions:
        if stopped(m[0]):
            continue

        mid = None
        score = 0.9
        for title in erd_db.gen_texts(m[0], allcase):
            mid, score = erd_db.freebase_text(title, topn=topn)
            if mid is not None:
                break
        if mid is None:
            continue
        entities.append((m[1], m[2],
            mid, second_id(mid), m[0], score, 0.99))
    # filter less popular texts
    mentioned = set()
    for e in entities:
        if e[-2] >= 0.9:
            mentioned.add(e[2])
    filtered = []
    for e in entities:
        if e[2] in mentioned:
            filtered.append(e)
    return filter_over(filtered), []
 
def create_response(textID, entities):
    text = ''
    for e in entities:
        text += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                textID, e[0], e[1], e[2], e[3], e[4], e[5], e[6])
    return text

def create_short_response(textID, entities):
    text = ''
    for e in entities:
        text += '{}\t0\t{}\t{}\t{}\n'.format(textID, e[2], e[4], e[5])
    return text

def shared_process(runID, textID, Text, allcase=False):

    params = runID.split(',')
    runID = params[0]
    if len(params) < 2:
        topn = 1
    else:
        topn = int(params[1])

    if len(params) < 3:
        tagme = 1
    else:
        tagme = float(params[2])

    if len(params) < 4:
        dbp = 0.25
    else:
        dbp = float(params[3])

    if len(params) < 5:
        dbpc = 0.3
    else:
        dbpc = float(params[4])

    fdbp = False
    if runID.find('gd') != -1:
        method = greedy_process
    elif runID.find('tg') != -1:
        method = tagme_process
    elif runID.find('dbp') != -1:
        method = dbpedia_process
        fdbp = True
    elif runID.find('mg') != -1:
        method = merge_process
    else:
        method = greedy_process

    c = runID.count('+')
    if c == 0:
        add = False
        more = False
    elif c == 1:
        add = True
        more = False
    elif c == 2:
        add = False
        more = True
    elif c >= 3:
        add = True
        more = True

    c = runID.count('-')
    if c == 0:
        remove = False
    elif c >= 1:
        remove = True

    both = runID.count('*')

    c = runID.count('r')
    reverse = not c == 0

    c = runID.count('f')
    ft = not c == 0

    print('rundID: {}, topn: {}, tagme: {}, dbp: {}, dbpc: {}, both: {}'.format(runID, topn, tagme, dbp, dbpc, both))
    print('method: {}, add: {}, more: {}, remove: {}, reverse: {}, ft: {}'.format(method.__name__, add, more, remove, reverse, ft))

    processed, _ = method(Text, textID,
            allcase=allcase, topn=topn,
            add=add, more=more, remove=remove,
            both=both,
            reverse=reverse,
            ft=ft,
            tagme=tagme,
            dbp=dbp,
            fdbp=fdbp,
            dbpc=dbpc)
    return processed

def get_vars(form):
    return form['runID'], form['TextID'], form['Text']
 
@app.route('/longTrack', methods = ['POST', 'GET'])
def long_track():
    runID, textID, Text = get_vars(request.form)

    processed = shared_process(runID, textID, Text)
    log_data('long', runID, textID, processed)
 
    res = create_response(textID, processed)
 
    return Response(res, content_type='text/plain; charset=utf-8')

@app.route('/shortTrack', methods = ['POST', 'GET'])
def short_track():
    runID, textID, Text = get_vars(request.form)

    processed = shared_process(runID, textID, Text, allcase=True)
    log_data('short', runID, textID, processed)

    res = create_short_response(textID, processed)
 
    return Response(res, content_type='text/plain; charset=utf-8')

@app.route('/ntunlp', methods = ['POST', 'GET'])
def get_data():
    runID, textID, Text = get_vars(request.form)

    save_data(textID, Text)
    
    return Response('', content_type='text/plain; charset=utf-8')

def save_data(textID, Text):
    if textID != '' and args.get_dir is not None:
        if os.path.isdir(args.get_dir):
            with open(os.path.join(args.get_dir, textID), 'w') as f:
                f.write(Text)

def log_data(track, runID, textID, mentions):
    info = '{}\t{}\t{}\t{}'.format(track, runID, textID, json.dumps(mentions))
    with open('log.log', 'a') as f:
        f.write(info + '\n')
    print(info)

def process_commands():
    parser = argparse.ArgumentParser(description='ERD 2014 - NTU NLP.')
    parser.add_argument('-get', dest='get_dir', metavar='OUTPUT-DIR',
            help='Store query data')
    parser.add_argument('-l', dest='db_path', metavar='DB-PATH',
            required=True,
            help='Load SQLite3 database.')
    parser.add_argument('-t', dest='tagme_path', metavar='TAGME-DICT-PATH',
            required=True)
    parser.add_argument('-d', dest='dbp_path', metavar='DBPEDIA-DICT-PATH',
            required=True)
    parser.add_argument('-p', dest='port', metavar='PORT',
            type=int, default=8082)
    return parser.parse_args()
 
if __name__ == '__main__':
    args = process_commands()

    erd_db = db.Database()
    erd_db.open(args.db_path)
    db_at = annotate.DbpediaAnnotator(args.dbp_path)
    tg_at = annotate.TagMeAnnotator(args.tagme_path)

    app.run(debug = True, use_reloader=False, host = '0.0.0.0', port = args.port)
