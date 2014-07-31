import json
import os.path

import requests

import api_key

DBPEDIA_QUERY = 'http://spotlight.dbpedia.org/rest/annotate/'
TAGME_QUERY = 'http://tagme.di.unipi.it/tag'

class Annotator(object):
    def __init__(self, path):
        self.entity_dict = {}
        if path is not None:
            with open(path, 'r') as f:
                for l in f:
                    key, value = l.split('\t')
                    self.entity_dict[key] = value.strip()

    def seperate_by_freebase(self, items, db):
        inItems, outItems = [], []
        for entry in items:
            if entry['mid'] is None or entry['mid'] not in db.id_dict:
                outItems.append(entry)
            else:
                inItems.append(entry)

        return inItems, outItems

    def get_freebase_id(self, eid):
        if eid in self.entity_dict:
            return self.entity_dict[eid]
        else:
            return None

class TagMeAnnotator(Annotator):
    
    def __init__(self, path):
        self.entity_dict = {}
        if path is not None:
            with open(path, 'r') as f:
                for l in f:
                    key, value = l.split('\t')
                    self.entity_dict[int(key)] = value.strip()

    def raw_annotate(self, text, textID):
        fdir = 'tagme'
        if not os.path.exists(fdir):
            os.mkdir(fdir)
        fpath = os.path.join(fdir, textID)
        if os.path.exists(fpath):
            with open(fpath, 'r') as f:
                jtext = f.read()
        else:
            try:
                with open(fpath, 'w') as f:
                    r = requests.post(TAGME_QUERY,
                            data={'text': text, 'key': api_key.TAGME_API_KEY}, headers={'accept': 'application/json'})
                    f.write(r.text)
                    jtext = r.text
            except:
                print('Error: {}'.format(textID))

        items = []
        try:
            jobj = json.loads(jtext)
            for entry in jobj['annotations']:
                offset = len(text[:int(entry['start'])].encode('utf8'))
                etext = entry['spot']
                items.append({
                    'mid': self.get_freebase_id(int(entry['id'])),
                    'offset': (offset, offset+len(etext.encode('utf8'))),
                    'text': etext,
                    'score': float(entry['rho'])
                    })
        except:
            print(textID)
        return items

class DbpediaAnnotator(Annotator):

    def __init__(self, path):
        super().__init__(path)

    def raw_annotate(self, text, textID, dbpc=0.3):
        fdir = 'dbpedia-{}'.format(dbpc)
        if not os.path.exists(fdir):
            os.mkdir(fdir)
        fpath = os.path.join(fdir, textID)
        if os.path.exists(fpath):
            with open(fpath, 'r') as f:
                jtext = f.read()
        else:
            try:
                with open(fpath, 'w') as f:
                    r = requests.post(DBPEDIA_QUERY,
                            data={'text': text, 'confidence': dbpc}, headers={'accept': 'application/json'})
                    f.write(r.text)
                    jtext = r.text
            except:
                print('Error: {}'.format(textID))

        items = []
        try:
            jobj = json.loads(jtext)
            for entry in jobj['Resources']:
                offset = len(text[:int(entry['@offset'])].encode('utf8'))
                etext = entry['@surfaceForm']
                items.append({
                    'mid': self.get_freebase_id(entry['@URI']),
                    'offset': (offset, offset+len(etext.encode('utf8'))),
                    'text': etext,
                    'score': float(entry['@similarityScore']),
                    'popularity': float(entry['@support']),
                    })
        except:
            print(textID)
        return items
