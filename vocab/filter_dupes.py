import srsly, plac, json

def main(loc):
    data = list(srsly.read_jsonl(loc))
    seen = set()
    for eg in data:
        if eg["text"] not in seen:
            print(json.dumps(eg))
            seen.add(eg["text"])


if __name__ == "__main__":
    plac.call(main)
