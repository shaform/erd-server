"""
jcount.py
Insert counts into sqlite3 database.

Usage:
    jcount.py SOURCE DEST
    where SOURCE = path of count
          DEST   = path of db file
"""
import sqlite3
import sys
import html.parser

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit()

conn = sqlite3.connect(sys.argv[2])
c = conn.cursor()

print('building mapping...')
mapping = {}
c.execute('SELECT id, mid FROM entity')
for x in c.fetchall():
    mapping[x[1]] = x[0]

print('extracting counts...')
entries = []
with open(sys.argv[1], 'r') as tsv:
    for l in tsv:
        mid, count = l.split('\t')
        count = int(count)
        entries.append((mapping[mid], count))

c.execute('''DROP TABLE IF EXISTS count''')
c.execute('''CREATE TABLE count
        (id INTEGER NOT NULL,
        count INTEGER NOT NULL,
        FOREIGN KEY(id) REFERENCES entity(id),
        UNIQUE(id))''')

print('inserting {} entries...'.format(len(entries)))
c.executemany('INSERT INTO count(id, count) VALUES (?,?)', entries)
print('inserted')
conn.commit()
conn.close()
