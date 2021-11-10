import plac
import json


def main(loc):
    for line in open(loc):
        if not line.strip():
            continue
        rank, text, freq = line.split()
        print(json.dumps({"text": text, "rank": int(rank), "freq": int(freq)}))

if __name__ == '__main__':
    plac.call(main)
