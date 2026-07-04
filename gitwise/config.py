"""Central config for GitWise CLI."""
import os
from pathlib import Path

# Where cloned repos live
REPO_CACHE_DIR = Path(os.environ.get("GITWISE_REPO_CACHE", Path.home() / ".gitwise" / "repos"))

# Where the vector DB persists
VECTOR_DB_DIR = Path(os.environ.get("GITWISE_DB_DIR", Path.home() / ".gitwise" / "vector_db"))

# Embedding model (local, free, no API key needed)
EMBEDDING_MODEL = os.environ.get("GITWISE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# LLM settings (Groq — free tier, cloud-hosted, fast)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
LLM_MODEL = os.environ.get("GITWISE_LLM_MODEL", "llama-3.3-70b-versatile")

# Chunking
CHUNK_SIZE_CHARS = 1500
CHUNK_OVERLAP_CHARS = 200

# Which files/dirs to index in v1 (keep it simple, per the plan)
PRIORITY_FILES = [
    "README.md", "README.rst", "readme.md",
    "CONTRIBUTING.md", "package.json", "requirements.txt",
    "pyproject.toml", "pom.xml", "Cargo.toml", "go.mod",
]
PRIORITY_DIRS = ["docs"]

# Source file extensions we'll chunk & embed
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
    ".rb", ".php", ".c", ".cpp", ".h", ".hpp", ".md", ".rst",
    ".yaml", ".yml", ".toml", ".json",
}

# Skip noisy directories
IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    "dist", "build", ".next", "target", "vendor", ".idea", ".vscode",
}

MAX_FILE_SIZE_BYTES = 300_000  # skip huge generated files
MAX_FILES_TO_INDEX = 500       # v1 safety cap
