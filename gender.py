import json, plac

MASC_ENDINGS = [
    "ant",
    "ast",
    "ich",
    "ig",
    "ismus",
    "ling",
    "or",
    "us"
]

FEM_ENDINGS = [
    "a",
    "anz",
    "ei",
    "anz",
    "ei",
    "enz",
    "heit",
    "ie",
    "ik",
    "in",
    "keit",
    "schaft",
    "sion",
    "taet",
    "tion"
    "ung",
    "ur"
]

NEUT_ENDINGS = [
    "chen",
    "lein",
    "ma",
    "ment",
    "sel",
    "tel",
    "tum",
    "um"
]

EXCEPTIONS = {
    "Labor": "das",
    "Genus": "das",
    "Tempus": "das",
    "Sofa": "das",
    "Genie": "das",
    "Atlantik": "der",
    "Pacific": "der",
    "derosaik": "das",
    "Abitur": "das",
    "dieutur": "das",
    "Purpur": "das",
    "dieirma": "die",
    "Streusel": "der",
    "Irrtum": "das",
    "Reichtum": "der",
    "Konsum": "der",
    "Protein": "das"
}

def has_ending(word, endings):
    return any(word.endswith(ending) for ending in endings)


def predict_gender(noun):
    if noun in EXCEPTIONS:
        return EXCEPTIONS[noun]
    elif len(noun) < 5:
        return None
    elif has_ending(noun, MASC_ENDINGS):
        return "der"
    elif has_ending(noun, FEM_ENDINGS):
        return "die"
    elif has_ending(noun, NEUT_ENDINGS):
        return "das"


def main(vocab_loc):
    words = [json.loads(line) for line in open(vocab_loc)]
    true = 0.
    false = 0.
    total = 0.

    for word in words:
        guess = predict_gender(word["text"])
        total += 1
        if guess is not None:
            if guess == word["gender"].lower():
                true += 1
            else:
                print(word["gender"], word["text"], "nicht", guess)
                false += 1
        else:
            print(word["gender"], word["text"])
    print(true / (true+false))
    print(false / (true+false))
    print((true+false) / total)


if __name__ == '__main__':
    plac.call(main)
