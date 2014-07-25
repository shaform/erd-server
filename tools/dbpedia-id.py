"""
dbpedia-id.py
Usage:
    dbpedia-id.py ENTITY DBPEDIA-LINKS OUTPUT
"""
import re
import sys 
import fileinput

from collections import defaultdict

if len(sys.argv) != 4:
    print(__doc__)
    sys.exit()

mids = set()
dbp_map = dict()

with open(sys.argv[1], 'r') as f:
    for l in f:
        mid = l.split('\t')[0]
        mids.add(mid)

with open(sys.argv[2], 'r') as f:
    for l in f:
        if not l.startswith('#'):
            tks = l.split(' ')
            dbp_id = tks[0][1:-1]
            mid = tks[2][1:-1]
            idx = mid.find('/ns/m.')
            if idx != -1:
                mid = '/m/' + mid[idx+6:]
                if mid in mids:
                    dbp_map[dbp_id] = mid


with open(sys.argv[3], 'w') as f:
    for dbp_id, mid in dbp_map.items():
        f.write('{}\t{}\n'.format(dbp_id, mid))
