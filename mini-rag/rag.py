"""
Mini RAG: ask questions about the documents in ./docs.

How it works:
  1. Load every .md/.txt file in ./docs and split it into paragraph chunks.
  2. Build a TF-IDF index over the chunks (no embedding model needed).
  3. For each question, retrieve the top-k most similar chunks.
  4. Send the question + retrieved chunks to Claude and ask it to answer
     using only that context, citing the source files.

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python rag.py                           # interactive
  python rag.py "Why was Pluto demoted?"  # one-shot
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_DIR = Path(__file__).parent / "docs"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
TOP_K = 4


@dataclass
class Chunk:
    source: str
    text: str


def load_chunks(docs_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*")):
        if path.suffix not in {".md", ".txt"}:
            continue
        for para in path.read_text(encoding="utf-8").split("\n\n"):
            para = para.strip()
            if para and not para.startswith("#"):
                chunks.append(Chunk(source=path.name, text=para))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform(c.text for c in chunks)

    def search(self, query: str, k: int = TOP_K) -> list[tuple[Chunk, float]]:
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix)[0]
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top if scores[i] > 0]


def build_prompt(question: str, hits: list[tuple[Chunk, float]]) -> str:
    context = "\n\n".join(f"[{c.source}]\n{c.text}" for c, _ in hits)
    return (
        "Answer the question using ONLY the context below. "
        "If the context doesn't contain the answer, say you don't know. "
        "Cite the source file name in brackets after each claim.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )


def answer(client: anthropic.Anthropic, retriever: Retriever, question: str) -> str:
    hits = retriever.search(question)
    if not hits:
        return "I couldn't find anything relevant in the documents."
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": build_prompt(question, hits)}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first (https://console.anthropic.com).")

    chunks = load_chunks(DOCS_DIR)
    if not chunks:
        sys.exit(f"No .md or .txt files found in {DOCS_DIR}")
    retriever = Retriever(chunks)
    client = anthropic.Anthropic()
    print(f"Indexed {len(chunks)} chunks from {DOCS_DIR}\n")

    if len(sys.argv) > 1:
        print(answer(client, retriever, " ".join(sys.argv[1:])))
        return

    print("Ask a question (Ctrl+C to exit):")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q:
            print(answer(client, retriever, q), "\n")


if __name__ == "__main__":
    main()
