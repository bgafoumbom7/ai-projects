# Claude Chatbot

A minimal terminal chatbot built on the Claude API. Responses stream in as they're generated, and the full conversation is kept in memory so Claude can refer back to earlier turns.

## Run it

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python chatbot.py
```

Commands inside the chat:

- `/reset` — forget the conversation
- `/quit` — exit

Set `CLAUDE_MODEL` to use a different model, e.g. `export CLAUDE_MODEL=claude-haiku-4-5-20251001`.

## How it works

Each turn is appended to a `messages` list and the whole list is sent with every request. The `client.messages.stream()` context manager yields text chunks as they arrive, which are printed immediately and then joined into the assistant's turn for memory.

## Ideas to extend

- Save/load conversations to a JSON file
- Add tool use (e.g. a calculator or web search)
- Wrap it in a web UI with Flask or FastAPI
