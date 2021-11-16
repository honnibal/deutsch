from prodigy.util import INPUT_HASH_ATTR, set_hashes
import time


class Card:
    def __init__(self, data, get_options):
        data.setdefault("timestamp", int(time.time()))
        data.setdefault("history", [])
        data.setdefault("accuracy", 0.5)
        self.data = data
        self.id = data[INPUT_HASH_ATTR]
        self.get_options = get_options
        self.update_priority()

    @property
    def accuracy(self):
        return self.data["accuracy"]

    def update_priority(self):
        self.priority = (
            get_recency_priority(self.data) 
            * get_difficulty_priority(self.data)
        )

    def update(self, response, acceptance, timestamp):
        print("Update", self.data["text"], self.data["options"], response, acceptance)
        self.data["history"].append(response)
        self.data["accuracy"] *= 0.7
        self.data["accuracy"] += 0.3 * (acceptance == "accept")
        if timestamp is not None:
            self.data["timestamp"] = timestamp
        self.update_priority()

    def to_json(self):
        self.data["prev_options"] = self.data["options"]
        self.data["options"] = self.get_options(self.data)
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
    def __init__(self, cards, get_options):
        self.get_options = get_options
        self.queue = [Card(card, get_options) for card in cards]
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
                self.sort_queue()
                self.i = 0
            card = self.queue[self.i]
            self.i += 1
            data = card.to_json()
            data["html"] = " "  # to make html_template kick in
            yield data

    def sort_queue(self):
        for card in self.queue:
            card.update_priority()
        self.queue.sort(reverse=True)

    def update(self, batch, timestamp=True):
        if timestamp is True:
            timestamp = int(time.time())
        for card_data in batch:
            if card_data.get("answer") == "ignore" or True:
                # Auto answer 'ignore'
                answer = card_data["options"][card_data["accept"][0]]["text"]
                is_correct = answer == card_data["truth"]
                card_data["answer"] = "accept" if is_correct else "reject"
            print(card_data["options"], card_data["truth"])
            if "accept" not in card_data:
                card = self.index[card_data[INPUT_HASH_ATTR]]
                card.priority = 0.
            else:
                card = self.index[card_data[INPUT_HASH_ATTR]]
                card.update(card_data["accept"], card_data["answer"], timestamp or card_data["timestamp"])
        self.sort_queue()
        self.i = 0


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