"""
db.py
Convert entity.tsv to sqlite3 database.

Usage:
    db.py SOURCE DEST
    where SOURCE = path of entity.tsv
          DEST   = path of db file
"""
import re
import sqlite3
import sys

if len(sys.argv) != 3:
    print(__doc__)

conn = sqlite3.connect(sys.argv[2])
c = conn.cursor()

c.execute('''CREATE TABLE entity
        (id INTEGER PRIMARY KEY,
        mid TEXT UNIQUE NOT NULL,
        wiki TEXT NOT NULL)''')

def rep(s):
    return chr(int(s.group(1), 16))

print('extracting entities...')
entities = []
with open(sys.argv[1], 'r') as tsv:
    for l in tsv:
        mid, _, wiki = l.split('\t')
        mid = mid
        wiki = re.sub(r'\$([0-9A-Fa-f]{4})', rep,
                wiki[21:-2])
        entities.append((mid, wiki))

print('inserting entities...')
c.executemany('INSERT INTO entity(mid, wiki) VALUES (?,?)', entities)

conn.commit()
conn.close()
