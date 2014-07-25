"""test
test.py DB-PATH QUERY_TEXT
"""
import sys
import mention
import db

erd_db = db.Database()
erd_db.open(sys.argv[1])

print('start testing')
with open(sys.argv[2], 'r') as f:
    print(mention.greedy_detector(erd_db, f.read()))

while True:
    get = input()
    if len(get) == 0:
        break
    else:
        print(mention.greedy_detector(erd_db, get))
