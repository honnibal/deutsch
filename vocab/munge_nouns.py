import sys, re, json


def get_spans(lines):
    for line in lines:
        if "<span" in line:
            yield line


def process_entry(line):
    number = "(\d+)"
    translation = "(\w+)"
    gender = "(Der|Die|Das)"
    word = "(\w+)"
    plural = "((?:Der|Die|Das)? \w+)"
    pattern = f"{number}.\s+{translation}\s+&#8211;\s+{gender} {word}"
    line = line.replace('&nbsp;', ' ')
    line = line.replace('<b>', '')
    line = line.replace('<i>', '')
    line = line.replace('</b>', '')
    line = line.replace('</i>', '')
    if re.search(pattern, line):
        rank, translation, gender, word = re.search(pattern, line).groups()
        return {"rank": rank, "en": translation, "text": word, "gender": gender}
    else:
        return None


def main():
    lines = [line for line in sys.stdin]
    spans = get_spans(lines)
    vocab = [process_entry(line) for line in lines if "&#8211;" in line]
    for entry in vocab:
        if entry:
            print(json.dumps(entry))


if __name__ == '__main__':
    main()
