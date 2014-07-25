"""
page-id.py
Usage:
    page-id.py ENTITY PAGE-SQL OUTPUT
"""
import re
import sys 
import fileinput

from collections import defaultdict

if len(sys.argv) != 6:
    print(__doc__)
    sys.exit()

def rep(s):
    return chr(int(s.group(1), 16))

mids = []
page_map = dict()
wiki_map = dict()

with open(sys.argv[1], 'r') as f:
    for l in f:
        mid, title, enwiki = l.split('\t')
        enwiki = re.sub(r'\$([0-9A-Fa-f]{4})', rep, enwiki[21:-2]).replace(' ', '_')
        wiki_map[enwiki] = mid
        mids.append(mid)

BEG = 'INSERT INTO `page` VALUES '

with open(sys.argv[2], 'r') as f:
    for l in f:
        if l.startswith(BEG):
            l = '),' + l[len(BEG):-2]
            entries = l.split('),(')
            for e in entries:
                if e == '':
                    continue
                try:
                    tks = e.split(',')
                    if int(tks[1]) == 0:
                        page_id = int(tks[0])
                        escapedR = re.compile(r'\\([\\\"\'])')
                        title = e[e.find('\'')+1:e.find('\',\'')]
                        title = escapedR.sub(r"\1", title)
                        if title in wiki_map:
                            page_map[page_id] = wiki_map[title]
                except:
                    print(tks)
                    sys.exit()

with open(sys.argv[3], 'w') as f:
    for page_id, mid in page_map.items():
        f.write('{}\t{}\n'.format(page_id, mid))
