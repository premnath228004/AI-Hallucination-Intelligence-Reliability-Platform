PROMPT_VERSION = "v1"

STRATEGIES = ("basic", "improved", "rag")

BASIC_TEMPLATE = "{question}"

IMPROVED_TEMPLATE = (
    "You are a careful assistant. Answer using only facts you are confident about.\n"
    "If you are not sure, if the question contains a false assumption, or if the information "
    "cannot be known, say clearly that you cannot answer reliably and explain why. Do not guess.\n"
    "Keep the answer short.\n\n"
    "Question: {question}\nAnswer:"
)

RAG_TEMPLATE = (
    "Answer the question using ONLY the context below. If the context does not contain the answer, "
    "say that the context is insufficient. Do not use outside knowledge.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\nAnswer:"
)


def build_prompt(strategy: str, question: str, context: str | None = None) -> str:
    if strategy == "basic":
        return BASIC_TEMPLATE.format(question=question)
    if strategy == "improved":
        return IMPROVED_TEMPLATE.format(question=question)
    if strategy == "rag":
        return RAG_TEMPLATE.format(context=context or "(no passages retrieved)", question=question)
    raise ValueError(f"Unknown strategy: {strategy}")