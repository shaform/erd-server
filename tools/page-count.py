"""
page-count.py
Usage:
    page-count.py ENTITY PAGE-COUNT OUTPUT
"""
import re
import sys 
import fileinput

from collections import defaultdict

if len(sys.argv) != 4:
    print(__doc__)
    sys.exit()

def rep(s):
    return chr(int(s.group(1), 16))

mids = []
page_count = defaultdict(int)
wiki_map = dict()

with open(sys.argv[1], 'r') as f:
    for l in f:
        mid, title, enwiki = l.split('\t')
        enwiki = re.sub(r'\$([0-9A-Fa-f]{4})', rep, enwiki[21:-2]).replace(' ', '_')
        wiki_map[enwiki] = mid
        mids.append(mid)

with open(sys.argv[2], 'r') as f:
    for l in f:
        _, enwiki, count = l.split()
        if enwiki in wiki_map:
            page_count[wiki_map[enwiki]] = int(count)

zeros = 0
with open(sys.argv[3], 'w') as f:
    for mid in mids:
        count = page_count[mid]
        if count == 0:
            zeros += 1
        f.write('{}\t{}\n'.format(mid, page_count[mid]))
print('totally {} zero counts'.format(zeros))
