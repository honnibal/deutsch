from heapq import heapify, nlargest, nsmallest, heappush

import srsly
import time
from prodigy import recipe
from prodigy.components.db import connect
from prodigy.util import INPUT_HASH_ATTR, set_hashes, prints
from prodigy.components.loaders import JSONL
from prodigy.components.filters import filter_duplicates
from prodigy.components.db import Example


def get_rank_priority(data):
    return 0.1 * (1. / float(data["rank"]))


def get_recency_priority(data):
    seconds_since_seen = int(time.time()) - data["timestamp"]
    if seconds_since_seen < 5:
        return 0.0
    elif seconds_since_seen < 20:
        return 0.1
    elif seconds_since_seen < 60:
        return 0.2
    elif seconds_since_seen < 600:
        return 0.3
    elif seconds_since_seen < 6000:
        return 0.4
    elif seconds_since_seen < 60000:
        return 0.5
    elif seconds_since_seen < 600000:
        return 0.6
    elif seconds_since_seen < 6000000:
        return 0.7
    else:
        return 0.8


def get_difficulty_priority(data):
    return 0.6 * (1-data["accuracy"])


class Card:
    def __init__(self, data):
        data.setdefault("timestamp", int(time.time()))
        data.setdefault("history", [])
        data.setdefault("accuracy", 0.5)
        self.data = data
        self.id = data[INPUT_HASH_ATTR]
        self.update_priority()

    @property
    def accuracy(self):
        return self.data["accuracy"]

    def update_priority(self):
        self.priority = (
            get_recency_priority(self.data) 
            * get_difficulty_priority(self.data)
        )

    def update(self, response, acceptance):
        self.data["history"].append(response)
        self.data["accuracy"] *= 0.7
        self.data["accuracy"] += 0.3 * (acceptance == "accept")
        self.update_priority()

    def to_json(self):
        self.data["priority"] = self.priority
        self.data["meta"] = {
            "priority": "%.2f" % self.priority,
            "rank": int(self.data.get("rank", 0)),
            "recency": "%.1f" % get_recency_priority(self.data),
            "accuracy": "%.2f" % self.data["accuracy"]
        }
        return self.data

    def __eq__(self, other):
        return self.priority == other.priority

    def __ne__(self, other):
        return self.priority != other.priority

    def __lt__(self, other):
        return self.priority < other.priority

    def __le__(self, other):
        return self.priority <= other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def __ge__(self, other):
        return self.priority >= other.priority


class CardQueue:
    def __init__(self, cards):
        self.queue = [Card(card) for card in cards]
        self.queue = self.queue
        self.index = {card.id: card for card in self.queue}
        self.i = 0
        self.progress = 0.

    @property
    def avg_accuracy(self):
        total_accuracy = sum(card.accuracy for card in self.queue)
        return total_accuracy / len(self.queue)

    def __iter__(self):
        self.i = 0
        self.sort_queue()
        while True:
            if self.i >= len(self.queue):
                print("Re-do queue", self.i, len(self.queue))
                self.sort_queue()
                self.i = 0
            card = self.queue[self.i]
            self.i += 1
            data = card.to_json()
            card.data["timestamp"] = int(time.time())
            data["html"] = " "  # to make html_template kick in
            yield data

    def sort_queue(self):
        for card in self.queue:
            card.update_priority()
        self.queue.sort(reverse=True)

    def update(self, batch):
        for card_data in batch:
            if "accept" not in card_data:
                card = self.index[card_data[INPUT_HASH_ATTR]]
                card.priority = 0.
            else:
                card = self.index[card_data[INPUT_HASH_ATTR]]
                card.update(card_data["accept"], card_data["answer"])
        self.sort_queue()
        self.i = 0


def add_gender_options(stream):
    for eg in stream:
        eg["options"] = [
            {"id": 1, "text": "der"},
            {"id": 2, "text": "die"},
            {"id": 3, "text": "das"},
        ]
        yield eg

 
@recipe("import_genders")
def import_genders(deck, jsonl_loc):
    DB = connect()
    cards = add_gender_options(srsly.read_jsonl(jsonl_loc))
    cards = list(filter_duplicates([set_hashes(card) for card in cards], by_input=True))
    DB.add_dataset(deck)
    DB.add_examples(list(cards), [deck])
    DB.save()


@recipe("mark-gender")
def mark_genders(dataset, jsonl_loc):
    stream = list(add_gender_options(srsly.read_jsonl(jsonl_loc)))
    DB = connect()
    return {
        "view_id": "choice",
        "dataset": dataset,
        "stream": stream,
        "update": None,
        "config": {
            "auto_exclude_current": True,
            "choice_auto_accept": True,
        },
    }

@recipe("add-noun")
def add_noun(deck, article, noun, accuracy=0.1):
    DB = connect()
    card = {
        "text": noun,
        "gender": article.lower(),
        "accuracy": accuracy,
        "timestamp": time.time(),
        "history": []
    }
    card = set_hashes(card)
    DB.add_examples([card], [deck])
    DB.save()
    prints("Successfully added %s %s" % (article, noun))


@recipe("set-gender")
def set_gender(dataset_in, dataset_out):
    """After marking the genders, set the answers into the 'gender' key."""
    DB = connect()
    examples = list(DB.get_dataset(dataset_in))
    examples = [eg for eg in examples if eg["answer"] == "accept" and eg.get("accept")]
    for eg in examples:
        eg.pop("answer")
        accept = eg.pop("accept")[0]
        eg["gender"] = ["der", "die", "das"][accept-1]
    DB.add_dataset(dataset_out)
    DB.add_examples(examples, [dataset_out])


def update_state(DB, name, cards):
    DB.drop_dataset(name)
    DB.add_dataset(name)
    DB.add_examples([card.to_json() for card in cards], [name])


HTML_TEMPLATE = """<span style="font-size: {{theme.largeText}}px"><span class="srs-article" style="width: 2em; text-align: right; display: inline-block; font-weight: bold; margin-right: 5px"></span> {{text}}</span>"""

JAVASCRIPT = """
document.addEventListener('prodigyupdate', ({ detail }) => {
    const accept = detail.task.accept || []
    if (accept.length) {
        const article = document.querySelector('.srs-article')
        const opt = detail.task.options.find(({ id }) => id === accept[0])
        const isCorrect = detail.task.gender.toLowerCase() === opt.text
        article.textContent = detail.task.gender.toLowerCase()
        article.style.color = isCorrect ? window.prodigy.theme.accept : window.prodigy.theme.reject

    }
})
"""


@recipe("srs")
def srs(deck):
    DB = connect()
    stream = CardQueue(list(add_gender_options(DB.get_dataset(deck))))
    return {
        "view_id": "choice",
        "dataset": f"raw_answers_{deck}",
        "stream": stream,
        "update": stream.update,
        "on_exit": lambda self: update_state(DB, deck, stream.queue),
        "progress": lambda *args, **kwargs: stream.avg_accuracy,
        "config": {
            "auto_exclude_current": False,
            "choice_auto_accept": False,
            "javascript": JAVASCRIPT,
            "html_template": HTML_TEMPLATE,
            "instructions": "instructions.html"
        },
    }
