"""Extractive summarizer: TF-IDF + sentence scoring. Pure Python, no downloads needed."""
import math
import re
from collections import Counter

STOPWORDS = set("""a about above after again against all am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has have having
he her here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not
now of off on once only or other our ours ourselves out over own same she should so some such than that the their
theirs them themselves then there these they this those through to too under until up very was we were what when
where which while who whom why will with would you your yours yourself yourselves also may might must shall via
per among within without upon however therefore thus""".split())

ABBREVIATIONS = ("mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "inc", "ltd", "no", "fig", "e.g", "i.e")


def split_sentences(text):
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])", text)
    sentences = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # glue back splits caused by common abbreviations (e.g. "Dr. Smith")
        if sentences and sentences[-1].lower().rstrip(".").split(" ")[-1] in ABBREVIATIONS:
            sentences[-1] += " " + p
        else:
            sentences.append(p)
    return sentences


def tokenize(sentence):
    words = re.findall(r"[a-zA-Z][a-zA-Z'\-]+|\d+", sentence.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def summarize(text, ratio=0.3, max_sentences=None):
    """Return dict with summary, selected indices and all sentences with scores."""
    sentences = split_sentences(text)
    n = len(sentences)
    if n == 0:
        return {"summary": "", "sentences": [], "selected": []}

    tokenized = [tokenize(s) for s in sentences]

    # document frequency over sentences (each sentence = one "document")
    df = Counter()
    for toks in tokenized:
        df.update(set(toks))
    idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}

    scores = []
    for i, toks in enumerate(tokenized):
        if not toks:
            scores.append(0.0)
            continue
        tf = Counter(toks)
        tfidf = sum((c / len(toks)) * idf[w] for w, c in tf.items())
        # sentence scoring: favour informative-length sentences and early position
        length_factor = min(len(toks), 20) / 20
        position = 1.0 + (0.25 if i == 0 else 0.1 if i < max(2, n // 10) else 0.0)
        scores.append(tfidf * (0.5 + length_factor) * position)

    k = max(1, round(n * ratio))
    if max_sentences:
        k = min(k, max_sentences)
    k = min(k, n)

    ranked = sorted(range(n), key=lambda i: scores[i], reverse=True)[:k]
    selected = sorted(ranked)
    summary = " ".join(sentences[i] for i in selected)
    return {
        "summary": summary,
        "selected": selected,
        "sentences": [{"text": s, "score": round(scores[i], 4)} for i, s in enumerate(sentences)],
    }
