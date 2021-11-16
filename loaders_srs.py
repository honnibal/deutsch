from prodigy.components.db import connect
from prodigy import recipe
from prodigy.components.filters import filter_duplicates
from prodigy.util import set_hashes
import srsly


@recipe("import-genders")
def import_genders(deck, jsonl_loc):
    """Import genders data from a jsonl, setting up a 'deck' of questions from them that can be used with the srs recipe."""
    DB = connect()
    cards = add_gender_options(srsly.read_jsonl(jsonl_loc))
    cards = list(filter_duplicates([set_hashes(card) for card in cards], by_input=True))
    DB.add_dataset(deck)
    DB.add_examples(list(cards), [deck])
    DB.save()

    
@recipe("import-verb-auxiliaries")
def import_verbs(deck, json_loc):
    """Import verb auxiliary data from a jsonl, setting up a 'deck' of questions from them that can be used with the srs recipe."""
    DB = connect()
    cards = add_auxiliary_options(srsly.read_json(json_loc))
    cards = list(filter_duplicates([set_hashes(card) for card in cards], by_input=True))
    DB.add_dataset(deck)
    DB.add_examples(list(cards), [deck])
    DB.save()
    

@recipe("import-glosses")
def import_glosses(deck, json_loc):
    """Create a srs dataset to learn glosses."""
    DB = connect()
    cards = add_dynamic_options(srsly.read_json(json_loc), truth_field="gloss", )
    cards = list(filter_duplicates([set_hashes(card) for card in cards], by_input=True))
    DB.add_dataset(deck)
    DB.add_examples(list(cards), [deck])
    DB.save()

    
@recipe("add-noun")
def add_noun(deck, article, noun, accuracy=0.1):
    DB = connect()
    card = {
        "text": noun,
        "gender": article.lower(),
        "gloss": "<gloss>",
        "accuracy": accuracy,
        "timestamp": time.time(),
        "history": []
    }
    card = set_hashes(card)
    DB.add_examples([card], [deck])
    DB.save()
    print("Successfully added %s %s" % (article, noun))


@recipe("add-verb-auxiliary")
def add_verb_auxiliary(deck, auxiliary, verb, accuracy=0.1):
    DB = connect()
    card = {
        "text": verb,
        "auxiliary": auxiliary.lower(),
        "truth": auxiliary.lower(),
        "gloss": "<gloss>",
        "accuracy": accuracy,
        "timestamp": time.time(),
        "history": []
    }
    card = set_hashes(card)
    DB.add_examples([card], [deck])
    DB.save()
    print("Successfully added %s %s" % (auxiliary, verb))


def add_dynamic_options(stream, truth_field: str):
    for eg in stream:
        eg["options"] = None
        eg["truth"] = eg[truth_field]
        yield eg


def add_gender_options(stream):
    for eg in stream:
        eg["options"] = [
            {"id": 1, "text": "der"},
            {"id": 2, "text": "die"},
            {"id": 3, "text": "das"},
        ]
        eg["truth"] = eg["gender"]
        eg.setdefault("gloss", "<gloss>")
        yield eg


def add_auxiliary_options(stream):
    for eg in stream:
        if isinstance(eg["perfect"], str):
            eg["text"] = eg["perfect"]
        else:
            eg["text"] = eg["perfect"][0]
        eg["options"] = [
            {"id": 1, "text": "ist", "inf": "sein"},
            {"id": 2, "text": "hat", "inf": "haben"},
            {"id": 3, "text": "hat/ist", "inf": "haben/sein"}
        ]
        if eg["auxiliary"] == "sein":
            eg["truth"] = "ist"
        elif eg["auxiliary"] == "haben":
            eg["truth"] = "hat"
        else:
            eg["truth"] = "hat/ist"
        eg.setdefault("gloss", "<gloss>")
        yield eg