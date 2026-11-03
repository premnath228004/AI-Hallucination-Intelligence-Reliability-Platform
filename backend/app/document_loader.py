import hashlib
import json
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT
from app.models import Chunk, Document

DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
MAX_CHARS = 200
OVERLAP_CHARS = 120
CHUNK_CONFIG = f"sentence-pack-{MAX_CHARS}-{OVERLAP_CHARS}"

SENTENCE_RE = re.compile(r"[^.!?]+[.!?]*\s*")


def chunk_text(text: str, max_chars: int = MAX_CHARS, overlap_chars: int = OVERLAP_CHARS) -> list[dict]:
    """Pack whole sentences into chunks of about max_chars.
    The last sentence of a chunk is repeated at the start of the next one if it is short enough (overlap).
    A single sentence longer than max_chars becomes its own chunk (it is never cut mid-sentence)."""
    spans = [(m.start(), m.end()) for m in SENTENCE_RE.finditer(text) if m.group().strip()]
    chunks, current, new_count = [], [], 0
    for span in spans:
        if new_count > 0 and (span[1] - current[0][0]) > max_chars:
            chunks.append((current[0][0], current[-1][1]))
            last = current[-1]
            current = [last] if (last[1] - last[0]) <= overlap_chars else []
            new_count = 0
        current.append(span)
        new_count += 1
    if new_count > 0:
        chunks.append((current[0][0], current[-1][1]))
    return [
        {"index": i, "start": s, "end": e, "text": text[s:e].strip()}
        for i, (s, e) in enumerate(chunks)
    ]


def load_corpus_file(db: Session, file_path: Path) -> dict:
    """Load a corpus JSON file. Safe to run repeatedly: no duplicates, no silent edits."""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    corpus = data["corpus"]
    stats = {
        "corpus": corpus,
        "chunk_config": CHUNK_CONFIG,
        "documents_inserted": 0,
        "documents_skipped": 0,
        "documents_rejected": 0,
        "chunks_inserted": 0,
        "messages": [],
    }
    for item in data.get("documents", []):
        key, content = item.get("doc_key"), item.get("content")
        if not key or not content:
            stats["documents_rejected"] += 1
            stats["messages"].append(f"Rejected item without doc_key or content: {item}")
            continue
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        existing = db.scalar(select(Document).where(Document.corpus == corpus, Document.doc_key == key))
        if existing is None:
            doc = Document(
                corpus=corpus,
                doc_key=key,
                title=item.get("title"),
                content=content,
                content_hash=content_hash,
                provenance=data.get("provenance"),
                relevant_question_ids=json.dumps(item.get("relevant_to_questions", [])),
            )
            db.add(doc)
            db.flush()  # gets doc.id
            for c in chunk_text(content):
                db.add(
                    Chunk(
                        document_id=doc.id,
                        chunk_config=CHUNK_CONFIG,
                        chunk_index=c["index"],
                        text=c["text"],
                        char_start=c["start"],
                        char_end=c["end"],
                    )
                )
                stats["chunks_inserted"] += 1
            stats["documents_inserted"] += 1
        elif existing.content_hash == content_hash:
            stats["documents_skipped"] += 1
        else:
            stats["documents_rejected"] += 1
            stats["messages"].append(
                f"{key}: content differs from the stored version. Create a new corpus version instead of editing."
            )
    db.commit()
    return stats
