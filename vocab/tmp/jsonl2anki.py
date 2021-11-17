import json, plac


def main(jsonl_loc):
    print("word; gender")
    for obj in [json.loads(line) for line in open(jsonl_loc)]:
        print(f"{obj['text']}; {obj['gender']}")


if __name__ == '__main__':
    plac.call(main)
