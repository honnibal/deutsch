from heapq import heapify, nlargest, nsmallest, heappush

import srsly
import time
import random
from prodigy import recipe
from prodigy.components.db import connect
from prodigy.util import INPUT_HASH_ATTR, set_hashes
from prodigy.components.loaders import JSONL
from prodigy.components.filters import filter_duplicates
from prodigy.components.db import Example

from libsrs import CardQueue


@recipe("srs")
def srs(deck: str, dynamic_options=0):
    DB = connect()
    raw_cards = list(DB.get_dataset(deck))
    if dynamic_options:
        get_options = get_dynamic_options(raw_cards, dynamic_options)
    else:
        get_options = lambda data: data["options"]
    stream = CardQueue(raw_cards, get_options)
    if f"raw_answers_{deck}" in DB.datasets:
        answers = list(DB.get_dataset(f"raw_answers_{deck}"))
        stream.update(answers, timestamp=None)
    return {
        "view_id": "choice",
        "dataset": f"raw_answers_{deck}",
        "stream": stream,
        "update": stream.update,
        "progress": lambda *args, **kwargs: stream.avg_accuracy,
        "config": {
            "auto_exclude_current": False,
            "choice_auto_accept": False,
            "javascript": JAVASCRIPT,
            "html_template": HTML_TEMPLATE,
            "instructions": "instructions.html"
        },
    }


def get_dynamic_options(raw_cards, n):
    truths = [c["truth"] for c in raw_cards]
    def get_option(card):
        items = random.sample(truths, n)
        if card["truth"] not in items:
            items[-1] = card["truth"]
        random.shuffle(items)
        return [
            {"id": i, "text": item}
            for i, item in enumerate(items)
        ]
    return get_option


def update_state(DB, name, cards):
    DB.drop_dataset(name)
    DB.add_dataset(name)
    DB.add_examples([card.to_json() for card in cards], [name])


HTML_TEMPLATE = """<span style="font-size: {{theme.largeText}}px"><span class="srs-article" style="width: 8em; text-align: right; display: inline-block; font-weight: bold; margin-right: 5px"></span> {{text}}</span><br/>"""
# <span "style="font-size: {{theme.smallText}}px">{{gloss}}</span>
JAVASCRIPT = """
document.addEventListener('prodigyupdate', ({ detail }) => {
    const accept = detail.task.accept || []
    if (accept.length) {
        const article = document.querySelector('.srs-article')
        const opt = detail.task.options.find(({ id }) => id === accept[0])
        const isCorrect = detail.task.truth.toLowerCase() === opt.text
        article.textContent = detail.task.truth.toLowerCase()
        article.style.color = isCorrect ? window.prodigy.theme.accept : window.prodigy.theme.reject

    }
})
"""