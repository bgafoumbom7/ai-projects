# Mini RAG

Retrieval-Augmented Generation in ~100 lines. Drop text files into `docs/`, ask questions, and Claude answers using only those documents — with citations.

Three sample documents are included (the solar system, coffee brewing, Python's history) so you can try it immediately.

## Run it

```bash
pip install anthropic scikit-learn
export ANTHROPIC_API_KEY=sk-ant-...
python rag.py "How hot should water be for brewing coffee?"
```

Run without arguments for an interactive prompt.

## How it works

1. **Chunk** — every `.md`/`.txt` file in `docs/` is split into paragraphs.
2. **Index** — chunks are vectorised with TF-IDF. This deliberately avoids a neural embedding model so there's nothing to download and the retrieval step is fully inspectable.
3. **Retrieve** — the question is vectorised the same way and the 4 most cosine-similar chunks are pulled.
4. **Generate** — the question and retrieved chunks are sent to Claude with instructions to answer only from that context and cite file names.

## Try asking

- "Why was Pluto reclassified?"
- "What ratio should I use for espresso?"
- "Who created Python and when did he step down?"
- "What is the capital of France?" — it should say it doesn't know.

## Ideas to extend

- Swap TF-IDF for sentence embeddings (e.g. `sentence-transformers`) for semantic matching
- Support PDFs with `pypdf`
- Persist the index so large document sets don't re-index every run
