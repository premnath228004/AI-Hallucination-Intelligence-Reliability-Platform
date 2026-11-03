import math
import re

EVALUATOR_VERSION = "reference-rules-v1"

ABSTENTION_PATTERNS = [
    r"\bi cannot\b", r"\bi can not\b", r"\bi can't\b", r"\bcannot answer\b",
    r"\bi do not have\b", r"\bi don't have\b", r"\bno information\b", r"\bno reliable\b",
    r"\bdoes not (?:contain|mention|say|provide|include)\b",
    r"\binsufficient\b", r"\bnot enough information\b",
]

PREMISE_REJECTION_PATTERNS = [
    r"\bnot three\b", r"\bno third\b", r"\bthere is no\b", r"\bdid not win\b",
    r"\bnever won\b", r"\bfalse premise\b", r"\bincorrect (?:premise|assumption)\b",
]


def _clean(text: str) -> str:
    return text.lower().replace("\u2019", "'")


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", _clean(text)).split())


def detect_abstention(text: str) -> bool:
    cleaned = _clean(text)
    return any(re.search(p, cleaned) for p in ABSTENTION_PATTERNS)


def detect_premise_rejection(text: str) -> bool:
    cleaned = _clean(text)
    return any(re.search(p, cleaned) for p in PREMISE_REJECTION_PATTERNS)


def reference_in_answer(reference: str, answer: str) -> bool:
    ref = normalize(reference)
    return bool(ref) and re.search(rf"\b{re.escape(ref)}\b", normalize(answer)) is not None


def _result(verdict, score, abstained, failure_category, needs_review, explanation):
    return {
        "verdict": verdict,
        "correctness_score": score,
        "abstained": abstained,
        "failure_category": failure_category,
        "needs_review": needs_review,
        "explanation": explanation,
    }


def evaluate_reference(*, answerable: bool, category: str | None, reference_answer: str | None, answer_text: str) -> dict:
    """Rule-based, reference-based check. It cannot understand meaning, so doubtful cases are flagged."""
    abstained = detect_abstention(answer_text)

    if answerable:
        matches = bool(reference_answer) and reference_in_answer(reference_answer, answer_text)
        if matches and not abstained:
            return _result("correct", 1.0, False, None, False, "Answer contains the reference answer.")
        if matches and abstained:
            return _result("correct", 1.0, True, None, True,
                           "Answer contains the reference but also an abstention phrase; check if it is hedged.")
        if abstained:
            return _result("incorrect_abstention", 0.0, True, "incorrect_abstention", False,
                           "Question is answerable but the answer declines to answer.")
        return _result("reference_mismatch", 0.0, False, "reference_mismatch", True,
                       "Answer does not contain the reference answer. It may be wrong or a valid paraphrase; the rules cannot tell. Manual review needed.")

    # Unanswerable question: the right behaviour is to abstain or reject the false premise.
    is_false_premise = category == "false_premise"
    rejected = is_false_premise and detect_premise_rejection(answer_text)
    if abstained or rejected:
        return _result("correct_abstention", 1.0, True, None, is_false_premise,
                       "Answer abstains or rejects the premise." + (" Premise rejections need manual confirmation." if is_false_premise else ""))
    return _result("failure_to_abstain", 0.0, False, "failure_to_abstain", is_false_premise,
                   "Question cannot be answered from evidence but the answer gives specific content without abstaining.")


def wilson_interval(successes: int, n: int, z: float = 1.96):
    """95% Wilson score interval for a proportion. Very wide when n is small."""
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)