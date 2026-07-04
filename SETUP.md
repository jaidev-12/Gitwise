# GitWise CLI — Setup

## 1. Install

```bash
git clone <your-repo-url>
cd Gitwise
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

This installs a `gitwise` command via the entry point in `pyproject.toml`.

**Note:** installing pulls in PyTorch, which by default grabs the GPU/CUDA
build (~2GB, slow). If `pip install -e .` seems to hang downloading huge
`nvidia_*` packages, you can Ctrl+C and install the much smaller CPU-only
build first, then retry:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e .
```

## 2. Get a free Groq API key (for `query` and `chat`)

We use [Groq](https://console.groq.com) — free tier, cloud-hosted, fast, no
cost to run. Sign up, grab a key, then:

```bash
export GROQ_API_KEY="gsk_..."
```

## 3. Get a free Hugging Face token (for the one-time embedding model download)

`gitwise index` downloads a small local embedding model
(`all-MiniLM-L6-v2`, ~90MB) the first time it runs. Get a free **read**
token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens),
then:

```bash
export HF_TOKEN="hf_..."
```

**Known issue:** on some networks the download can stall at 0% forever.
If that happens, this fixes it — force the plain HTTPS downloader instead
of HF's newer "Xet" protocol:

```bash
export HF_HUB_DISABLE_XET=1
```

## 4. Make these permanent (recommended)

Re-exporting these every new terminal gets old fast. Add them to your
shell profile once:

```bash
# if you use zsh (Kali's default):
echo 'export GROQ_API_KEY="gsk_..."' >> ~/.zshrc
echo 'export HF_HUB_DISABLE_XET=1' >> ~/.zshrc
source ~/.zshrc

# if you use bash instead:
echo 'export GROQ_API_KEY="gsk_..."' >> ~/.bashrc
echo 'export HF_HUB_DISABLE_XET=1' >> ~/.bashrc
source ~/.bashrc
```

Not sure which shell you're on? Run `echo $SHELL` — don't mix the two,
editing `.bashrc` while running zsh (or vice versa) does nothing useful.

## 5. Try it (this is issue #11's test case)

```bash
gitwise index https://github.com/tiangolo/fastapi --repo fastapi
gitwise chat --repo fastapi
```

`chat` drops you into an interactive loop — ask follow-up questions
without retyping `--repo` each time. Type `exit` or `quit` to leave.
For a single one-off question instead, use:

```bash
gitwise query "How does dependency injection work?" --repo fastapi
```

Embeddings run locally and are free after the first download; only
`query`/`chat` calls the Groq API.

Any public GitHub repo works, not just fastapi — just pick a different
`--repo` name per repo:

```bash
gitwise index https://github.com/psf/requests --repo requests
gitwise chat --repo requests
```

## How it maps to the issues

- **#2** Typer CLI scaffold → `gitwise/cli.py` (`index`, `query`, `chat` commands)
- **#8** `gitwise index <url>` with spinner + success panel → done, uses
  `rich.status.Status` + `rich.panel.Panel`
- **#10** `gitwise query "<question>" --repo <name>` with Markdown output →
  done, uses `rich.markdown.Markdown`
- **#11** Test against fastapi → verified: 2119 chunks indexed, correctly
  explained dependency injection with accurate source citations

## Project layout

```
gitwise/
  cli.py            # Typer commands (index, query, chat)
  config.py         # paths, model names, chunking constants
  core/
    cloner.py       # git clone + repo naming
    chunker.py      # walk files, split into chunks
    indexer.py      # ChromaDB build + query
    llm.py          # Groq call with retrieved context
requirements.txt
pyproject.toml
```

## Notes / things to tune together

- `config.py` has `SOURCE_EXTENSIONS`, `IGNORE_DIRS`, `MAX_FILES_TO_INDEX` —
  easy knobs if indexing is too slow/fast on big repos.
- Re-running `gitwise index` on the same repo name wipes and rebuilds that
  collection (idempotent). Use `--force` to also re-clone.
- `n_results` in `query`/`chat` controls how many chunks get sent to the
  LLM — tune this if answers feel thin or too noisy.
- Private repos and repos over 500 files aren't fully supported yet —
  good candidates for follow-up issues.
