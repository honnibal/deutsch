from prodigy import recipe
import srsly

def add_options(task, n=5):
    task["options"] = [{"id": str(i), "text": str(i)} for i in range(1, n)]
    task["options"].append({"id": f"{n}+", "text": f"{n}+"})
    return task


@recipe("syllables")
def syllables(dataset, vocab_jsonl):
    data = srsly.read_jsonl(vocab_jsonl)
    stream = [add_options(task) for task in data]
    return {
        "dataset": dataset,
        "view_id": "choice",
        "stream": stream,
        "config": {
          "choice_auto_accept": True,
          "choice_style": "single"
        }
    }
