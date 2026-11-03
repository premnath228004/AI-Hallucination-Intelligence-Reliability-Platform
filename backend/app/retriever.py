import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.document_loader import CHUNK_CONFIG
from app.models import Chunk, Document

DEFAULT_CORPUS = "pilot_corpus_v1"
RETRIEVER_NAME = "tfidf-v1"
RETRIEVER_DESCRIPTION = (
    "TF-IDF word-overlap retrieval with cosine similarity. "
    "This is lexical retrieval, NOT neural embeddings: it cannot match synonyms or paraphrases."
)


class TfidfRetriever:
    def __init__(self, items: list[dict]):
        if not items:
            raise ValueError("No chunks found. Load the document corpus first (POST /api/documents/load-sample).")
        self.items = items
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words="english")
        self.matrix = self.vectorizer.fit_transform([item["text"] for item in items])

    def search(self, query: str, k: int = 3) -> list[dict]:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        results = []
        for idx in scores.argsort()[::-1][:k]:
            if scores[idx] <= 0:
                break  # no word overlap at all: not a retrieval hit
            results.append({"rank": len(results) + 1, "score": round(float(scores[idx]), 4), **self.items[idx]})
        return results


def build_retriever(db: Session, corpus: str = DEFAULT_CORPUS, chunk_config: str = CHUNK_CONFIG) -> TfidfRetriever:
    rows = db.execute(
        select(Chunk, Document)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.corpus == corpus, Chunk.chunk_config == chunk_config)
        .order_by(Chunk.id)
    ).all()
    items = [
        {
            "chunk_id": c.id,
            "document_id": d.id,
            "doc_key": d.doc_key,
            "title": d.title,
            "chunk_index": c.chunk_index,
            "text": c.text,
        }
        for c, d in rows
    ]
    return TfidfRetriever(items)
def load_relevance_map(db: Session, corpus: str = DEFAULT_CORPUS) -> dict[str, set]:
    """question external_id -> set of document keys the corpus author marked as relevant."""
    relevant: dict[str, set] = {}
    for doc in db.scalars(select(Document).where(Document.corpus == corpus)).all():
        for qid in json.loads(doc.relevant_question_ids or "[]"):
            relevant.setdefault(qid, set()).add(doc.doc_key)
    return relevant