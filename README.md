# 🦉 GitWise

AI assistant that lets you chat with any public GitHub repo in plain English. Understand unfamiliar codebases faster with RAG-powered retrieval, hybrid search, and persistent conversation memory — all from your terminal.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey)

## 💬 Live Demo

```
You: how does dependency injection work?

GitWise:
📌 What This Repo Does
FastAPI's dependency injection is handled by the Depends function in
fastapi/param_functions.py. It allows you to declare a dependency that
runs when a route is called, and its return value is passed into the
route function.

Sources: fastapi/applications.py, fastapi/param_functions.py

You: what was my first question?

GitWise:
Your first question was: "how does dependency injection work?"
```

Ask a follow-up, and GitWise actually remembers the conversation — no re-explaining context every time.

## ✨ Features

### 🔍 Understanding

| Feature | How it works |
|---|---|
| Plain-English Q&A | Ask about any indexed repo in natural language, get beginner-friendly explanations |
| Source citations | Every answer names the exact files it drew from — no guessing where an answer came from |
| Structured answers | Responses use clear sections (What it does, Tech stack, Where to start, How to run it) only when relevant to the question asked |

### 🧠 Memory & Retrieval

| Feature | Detail |
|---|---|
| Conversation memory | Powered by LangGraph, checkpointed to local SQLite — quit and resume a conversation anytime |
| Hybrid search | Combines vector similarity (ChromaDB) with BM25 keyword search, fused via Reciprocal Rank Fusion — catches exact matches (function names, error strings) that pure vector search can miss |
| Question rewriting | Follow-up questions are automatically rewritten into standalone questions using chat history before retrieval runs |

### 🎨 Terminal Experience

| Feature | Detail |
|---|---|
| Branded intro | Animated git-graph → logo sequence on startup |
| Colored roles | Distinct colors for your questions vs. GitWise's answers |
| Rich output | Spinners, panels, and Markdown-rendered answers (tables, code blocks, lists) |

## 🚀 Installation

**Requirements:** Python 3.10+, Linux or macOS recommended

```bash
# Clone the repo
git clone https://github.com/jaidev-12/Gitwise.git
cd Gitwise

# Set up a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

### API keys (both free, no credit card)

```bash
# Groq — powers the actual Q&A (free tier)
# Get one at https://console.groq.com
export GROQ_API_KEY="gsk_..."

# Hugging Face — only needed once, to download the local embedding model
# Get one at https://huggingface.co/settings/tokens
export HF_TOKEN="hf_..."
```

See [SETUP.md](SETUP.md) for the full setup guide, including troubleshooting for common first-run issues.

## 🖥️ How It Works

```
GitHub URL
     │
     ▼
Clone repo (shallow clone, cached locally)
     │
     ▼
Chunk source files (overlapping windows, per-file)
     │
     ▼
Embed chunks (local model — sentence-transformers, no API cost)
     │
     ▼
Store in ChromaDB (persistent vector index)
     │
     ▼
   ... ask a question ...
     │
     ▼
Hybrid retrieval (vector search + BM25, fused via RRF)
     │
     ▼
LangGraph: rewrite → retrieve → generate
     │
     ▼
Groq LLM answers using only retrieved context
     │
     ▼
Conversation checkpointed to SQLite (persists across sessions)
```

## 📖 Usage

```bash
# Index a repo (one-time per repo)
gitwise index https://github.com/tiangolo/fastapi --repo fastapi

# Have an ongoing, memory-enabled conversation
gitwise chat --repo fastapi

# Or ask a single one-shot question
gitwise query "How does routing work?" --repo fastapi

# Start a fresh conversation instead of resuming the last one
gitwise chat --repo fastapi --new-session
```

## 📁 Project Structure

```
Gitwise/
├── gitwise/
│   ├── cli.py              # Typer commands: index, query, chat
│   ├── config.py           # Paths, model names, retrieval/memory settings
│   ├── core/
│   │   ├── cloner.py       # Git clone + repo naming
│   │   ├── chunker.py      # File discovery + chunking
│   │   ├── indexer.py      # ChromaDB vector index build/query
│   │   ├── retriever.py    # Hybrid vector + BM25 retrieval (RRF)
│   │   ├── llm.py          # Groq calls, system prompt, context building
│   │   └── branding.py     # Terminal intro animation, colored labels
│   ├── graph/
│   │   ├── chat_graph.py   # LangGraph: rewrite → retrieve → generate
│   │   └── state.py        # Shared graph state definition
│   └── memory/
│       └── checkpointer.py # SQLite-backed conversation persistence
├── pyproject.toml
├── requirements.txt
└── SETUP.md
```

## ⚙️ Configuration

Key settings live in `gitwise/config.py`:

```python
CHUNK_SIZE_CHARS = 1500       # characters per chunk
CHUNK_OVERLAP_CHARS = 200     # overlap between adjacent chunks
MAX_FILES_TO_INDEX = 500      # safety cap per repo
VECTOR_TOP_K = 10             # candidates from vector search before fusion
BM25_TOP_K = 10                # candidates from keyword search before fusion
MAX_HISTORY_MESSAGES = 12     # sliding window of turns kept in the prompt
```

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Typer + Rich | CLI framework and terminal UI |
| ChromaDB | Persistent vector database |
| sentence-transformers | Local, free text embeddings |
| BM25 (rank_bm25) | Keyword-based retrieval |
| LangGraph | Conversation state machine + memory |
| Groq | Free-tier LLM inference (Llama 3.3 70B) |
| SQLite | Conversation checkpointing |
| pyfiglet | ASCII logo rendering |

## 🗺️ Roadmap

- [ ] Support for private repositories (GitHub auth)
- [ ] Repos larger than the current 500-file cap
- [ ] Web/mobile interface (CLI is v1; originally planned as a longer-term option)
- [ ] Reranker node in the retrieval graph

## 🤝 Contributing

Contributions are welcome! Fork the repo, make your changes, and open a pull request.

Ideas for new features:
- Reranking retrieved chunks before generation
- Support for private repos
- Web UI
- Multi-repo comparison queries

## 👥 Contributors

- [@jaidev-12](https://github.com/jaidev-12) — Jaidev
- [@4ravind-b](https://github.com/4ravind-b) — Aravind B

## 📄 License

MIT — see [LICENSE](LICENSE)

## 📦 Releases

See the [Releases page](https://github.com/jaidev-12/Gitwise/releases) for version history and changelogs.

- **v2.0.0** — Conversation memory, hybrid retrieval, branded terminal UI
- **v1.0.0** — Initial working CLI: index, query, chat (no memory)
