# AI Projects

A collection of small, self-contained AI projects. Each folder is independent and has its own README.

| Project | What it does | Dependencies |
|---|---|---|
| [claude-chatbot](./claude-chatbot) | Terminal chatbot with streaming replies and conversation memory, built on the Claude API | `anthropic` |
| [sentiment-classifier](./sentiment-classifier) | Classic ML text classifier (TF-IDF + logistic regression) that labels reviews positive/negative | `scikit-learn` |
| [mini-rag](./mini-rag) | Retrieval-augmented generation: answers questions about your own documents | `scikit-learn`, `anthropic` |
| [tic-tac-toe-ai](./tic-tac-toe-ai) | Unbeatable tic-tac-toe opponent using the minimax algorithm | none |
| [azure-devops-log-reader](./azure-devops-log-reader) | CLI that reads Azure DevOps pipeline deployment logs, extracts errors, and asks Claude to diagnose failures | `requests`, `anthropic` (optional) |

## Getting started

```bash
git clone https://github.com/<your-username>/ai-projects.git
cd ai-projects
pip install -r requirements.txt
```

Projects that call the Claude API need an API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Get one at https://console.anthropic.com.

## License

MIT
