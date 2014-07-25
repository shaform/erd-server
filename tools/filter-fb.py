import re
import sys

from collections import defaultdict

if __name__ == '__main__':
    ts = []
    with open(sys.argv[1], 'r') as f:
        for l in f:
            ts.append(l.split('\t')[0].split('/')[2])

    pattern = re.compile('({})'.format('|'.join(ts)))

    td = defaultdict(int)
    for l in sys.stdin:
        for idx in pattern.findall(l):
            td[idx] += 1

    for k in td:
        print('/m/{}\t{}'.format(k, td[k]))
