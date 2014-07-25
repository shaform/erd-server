"""
conn.py
Connect to server and send requests.

Usage:
    conn.py [-s URL] [-u] [-i SOURCE] [-r RUNID]
    where URL = url of the server
          SOURCE = path of directory storing requests
          RUNID = run id of the server
          -u: use standard input instead of stored requests
"""
import argparse
import os

import requests

def process_commands():
    parser = argparse.ArgumentParser(description='Connect to server.')
    parser.add_argument('-u', dest='use_stdin', action='store_true',
            help='If specified, use standard input instead of SOURCE.')
    parser.add_argument('-s', dest='url', metavar='URL',
            default='http://0.0.0.0:8082/longTrack',
            action='store', help='The dest server url.')
    parser.add_argument('-i', dest='input_dir', metavar='SOURCE',
            action='store', help='The input requests directory.')
    parser.add_argument('-r', dest='run_id', metavar='RUNID',
            default='TestRun',
            action='store', help='The run id of the server.')
    return parser.parse_args()

def send_request(payload):
#    print('sending request to {}, payload={}'.format(args.url, payload))
    print('sending request to {}, TextID={}'.format(args.url, payload['TextID']))
    r = requests.post(args.url, data=payload)
    print(r.text)

if __name__ == '__main__':
    args = process_commands()

    payload = {'runID': args.run_id, 'TextID': 'testText',
            'Text': 'chris brown nicki minaj right by my side download\r\n'}

    if args.use_stdin:
        num = 0
        read = input()
        while not read.isspace() and read != '':
            payload['Text'] = read
            payload['TextID'] = 'Stdin-{}'.format(num)
            send_request(payload)
            num += 1
            read = input()
    elif args.input_dir is not None:
        flist = os.listdir(args.input_dir)
        for f in flist:
            payload['TextID'] = f
            with open(os.path.join(args.input_dir, f), 'rb') as f:
                payload['Text'] = f.read()
            send_request(payload)
    else:
        send_request(payload)
