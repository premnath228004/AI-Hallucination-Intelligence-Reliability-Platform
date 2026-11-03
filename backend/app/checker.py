import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from app.evaluator import detect_abstention

SUPPORTED_AT = 0.75  # combined overlap score at or above this: "supported"
RELEVANT_AT = 0.35   # below this the evidence is not about the sentence at all: "unverifiable"

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9]+")

LIMITATIONS = [
    "Word-overlap heuristic, not a fact checker. It does not understand meaning, negation or relations, so a wrong answer made of words found in the evidence can slip through.",
    "Labels are candidates for human review. A claim missing from the available evidence is 'unverifiable', not automatically a hallucination.",
    "Only the evidence you paste, or the small built-in corpus (11 short documents), is used. Most real-world questions will be unverifiable here.",
    "The reference check only works when the question matches a benchmark question.",
]


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text.strip()) if s.strip()]


def passages_from_text(text: str, source: str = "your evidence") -> list[dict]:
    """Single sentences plus neighbouring sentence pairs, so a claim can match either."""
    sentences = split_sentences(text)
    passages = []
    for i, sentence in enumerate(sentences):
        passages.append({"source": f"{source}, sentence {i + 1}", "text": sentence})
        if i + 1 < len(sentences):
            passages.append(
                {"source": f"{source}, sentences {i + 1}-{i + 2}", "text": f"{sentence} {sentences[i + 1]}"}
            )
    return passages


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower().replace("\u2019", "'"))


def _content(tokens: list[str]) -> set:
    return {t for t in tokens if t not in ENGLISH_STOP_WORDS}


def _bigrams(tokens: list[str]) -> set:
    return set(zip(tokens, tokens[1:]))


def _numbers(tokens: list[str]) -> set:
    return {t for t in tokens if t.isdigit()}


def _score(claim_tokens: list[str], passage_tokens: list[str]):
    content = _content(claim_tokens)
    unigram = len(content & _content(passage_tokens)) / len(content)
    if len(claim_tokens) >= 3:
        claim_bigrams = _bigrams(claim_tokens)
        bigram = len(claim_bigrams & _bigrams(passage_tokens)) / len(claim_bigrams)
        return 0.5 * unigram + 0.5 * bigram, unigram, bigram
    return unigram, unigram, None  # very short answers: word coverage only


def analyze_claim(sentence: str, passages: list[dict]) -> dict:
    base = {"sentence": sentence, "support_score": None, "unigram_coverage": None,
            "bigram_coverage": None, "best_passage": None, "missing_numbers": []}
    tokens = _tokens(sentence)
    if detect_abstention(sentence):
        return {**base, "label": "abstention",
                "explanation": "The sentence declines to answer, so it makes no factual claim to check."}
    if not _content(tokens):
        return {**base, "label": "not_checkable", "explanation": "The sentence has no checkable content words."}
    if not passages:
        return {**base, "label": "unverifiable", "explanation": "No evidence passages are available."}

    scored = sorted(
        ((*_score(tokens, _tokens(p["text"])), p) for p in passages), key=lambda item: item[0], reverse=True
    )
    best_score, best_uni, best_bi, best = scored[0]
    evidence_numbers = set()
    for score, _, _, passage in scored:
        if score >= RELEVANT_AT:
            evidence_numbers |= _numbers(_tokens(passage["text"]))
    missing = sorted(_numbers(tokens) - evidence_numbers)

    result = {
        **base,
        "support_score": round(best_score, 3),
        "unigram_coverage": round(best_uni, 3),
        "bigram_coverage": round(best_bi, 3) if best_bi is not None else None,
        "best_passage": {"source": best["source"], "text": best["text"]},
        "missing_numbers": missing,
    }
    if best_score < RELEVANT_AT:
        label = "unverifiable"
        why = "No passage covers this sentence well enough to check it. This is not proof that it is wrong."
    elif missing:
        label = "candidate_contradicted"
        why = (f"The relevant evidence does not contain the number(s) {', '.join(missing)} used in this "
               "sentence. The evidence may state a different value. Review.")
    elif best_score >= SUPPORTED_AT:
        label = "supported"
        why = "Most words and word pairs of the sentence appear in one evidence passage (lexical match only)."
    else:
        label = "candidate_unsupported"
        why = "The sentence overlaps with the evidence only partly. It may be unsupported, reworded or reversed. Review."
    return {**result, "label": label, "explanation": why}


def analyze_answer(answer: str, passages: list[dict]) -> dict:
    claims = [analyze_claim(s, passages) for s in split_sentences(answer)]
    counts: dict[str, int] = {}
    for claim in claims:
        counts[claim["label"]] = counts.get(claim["label"], 0) + 1
    if counts.get("candidate_contradicted") or counts.get("candidate_unsupported"):
        signal = "review_needed"
    elif counts.get("unverifiable"):
        signal = "unverifiable"
    elif counts.get("supported"):
        signal = "no_issue_detected"
    else:
        signal = "abstained_or_not_checkable"
    return {"signal": signal, "counts": counts, "claims": claims}