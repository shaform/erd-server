"""
jdict.py
Insert dictionary into sqlite3 database.

Usage:
    jdict.py SOURCE DEST
    where SOURCE = path of dictionary.tsv
          DEST   = path of db file
"""
import sqlite3
import sys
import html.parser

h = html.parser.HTMLParser()

if len(sys.argv) != 3:
    print(__doc__)

conn = sqlite3.connect(sys.argv[2])
c = conn.cursor()

print('building mapping...')
mapping = {}
c.execute('SELECT id, mid FROM entity')
for x in c.fetchall():
    mapping[x[1]] = x[0]

print('extracting entries...')
entries = []
with open(sys.argv[1], 'r') as tsv:
    for l in tsv:
        mid, title = l.split('\t')
        title = h.unescape(title[1:-5])
        entries.append((title, mapping[mid]))

entries = list(set(entries))
c.execute('''DROP TABLE IF EXISTS dict''')
c.execute('''CREATE TABLE dict
        (title TEXT NOT NULL,
        id INTEGER NOT NULL,
        FOREIGN KEY(id) REFERENCES entity(id),
        UNIQUE(title, id))''')

print('inserting {} entries...'.format(len(entries)))
c.executemany('INSERT INTO dict(title, id) VALUES (?,?)', entries)
print('inserted')
conn.commit()
conn.close()
