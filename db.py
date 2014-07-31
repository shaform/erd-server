"""Database management"""
import json
import os.path
import re
import sqlite3

import requests

import api_key

from collections import defaultdict
from itertools import combinations, chain

r_nW = re.compile(r'(\W+)')

FB_API_KEY = api_key.API_KEY
FB_QUERY = ('https://www.googleapis.com/freebase/v1/'
        + 'search?query={}&key=' + FB_API_KEY
        + '&limit=5'
        )

def all_subsets(ss):
      return chain(*map(lambda x: combinations(ss, x), range(0, len(ss)+1)))

def a_lower(t):
    if len(t) > 1:
        return t[0].lower() + t[1:]
    else:
        return t

def a_upper(t):
    if len(t) > 1:
        return t[0].upper() + t[1:]
    else:
        return t.upper()

def each_lower(ts):
    ts = list(ts)
    for i in range(len(ts)):
        ts[i] = a_lower(ts[i])
    return ts

def each_upper(ts):
    ts = list(ts)
    for i in range(len(ts)):
        ts[i] = a_upper(ts[i])
    return ts

class Database(object):
    def open(self, db_path):
        self.db_path = db_path
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        self.erd_dict = defaultdict(set)
        self.erd_total_dict = defaultdict(set)

        c.execute('select title, id from dict')

        for entry in c.fetchall():
            title, eid = entry
#            ts = each_lower(r_nW.split(title))
            ts = r_nW.split(title)
            lts = len(ts)
            for l in range(lts):
                if r_nW.match(ts[l]) is None or l == lts - 1:
                    key = ''.join(ts[:l+1])
                    if len(key) > 0:
                        self.erd_dict[key].add(eid)
            if len(key) > 0:
                self.erd_total_dict[key].add(eid)

        self.id_dict = {}
        c.execute('''select id, mid from entity''')
        for entry in c.fetchall():
            eid, mid = entry
            self.id_dict[eid] = mid
            self.id_dict[mid] = eid

        c.close()
        conn.close()

        self.qcache = {}
        if not os.path.exists('qcache'):
            open('qcache', 'a').close()
        with open('qcache', 'r') as f:
            for l in f:
                tks = l.split('\t')
                if len(tks) < 2:
                    continue
                key = tks[0]
                values = [ x.strip() for x in tks[1:]]
                self.qcache[key] = values

    def gen_texts(self, title, allcase=False):
        if allcase:
            tokens = r_nW.split(title)
            lowed = each_lower(tokens)
            upped = each_upper(tokens)
            diffed = []
            for idx in range(len(tokens)):
                if lowed[idx] != upped[idx]:
                    diffed.append(idx)
            titles = []
            for subset in all_subsets(diffed):
                newtks = list(upped)
                for idx in subset:
                    newtks[idx] = lowed[idx]
                titles.append(''.join(newtks))
        else:
            titles = [title]
        return titles

    def title_exist(self, title):
        return title in self.erd_dict

    def title_match(self, title):
        return title in self.erd_total_dict

    def freebase_text(self, text, topn=1):
        erd_dict = self.erd_total_dict
        if text not in erd_dict:
            return None, 0.9

        try:
            s = erd_dict[text]
            if text in self.qcache:
                results = self.qcache[text]
            else:
                results = requests.get(FB_QUERY.format(text)).json()['result']
                results = [ r['mid'] for r in results]
                self.qcache[text] = results
                with open('qcache', 'a') as f:
                    f.write('{}\t{}\n'.format(text, '\t'.join(results)))
            mid = None
            score = 0.9
            for rmid in results[:topn]:
                rmid_passed = False
                if rmid in self.id_dict:
                    if self.id_dict[rmid] in s:
                        rmid_passed = True
                if rmid_passed:
                    mid = rmid
                    break
                score -= 0.1
            return mid, score
        except Exception as e:
            print('error in freebase')
            print(e)
            return None, 0.1
