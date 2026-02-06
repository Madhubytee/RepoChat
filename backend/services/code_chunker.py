import os
from typing import List


CHUNK_SIZE = 50  # lines per chunk
OVERLAP = 10     # overlap lines between chunks

def chunk_code_file(file_path: str, repo_path: str) -> List[dict]:
    """Read a code file and split it into overlapping chunks."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except (OSError, IOError):
        return []

    if not lines:
        return []

    relative_path = os.path.relpath(file_path, repo_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    chunks = []

    if len(lines) <= CHUNK_SIZE: #if the file is small, we can just take it as one chunk without splitting
        content = "".join(lines)
        chunks.append({
            "content": content,
            "file_path": relative_path,
            "start_line": 1,
            "end_line": len(lines),
            "language": _get_language(file_ext),
        })
        return chunks

    start = 0 #splits the file into chucks with overlap, for example if chunk size is 50 and overlap is 10, the first chunk will be lines 1-50, the second chunk will be lines 41-90, the third chunk will be lines 81-130 and so on (this is to avaoid missing important prior context)
    while start < len(lines):
        end = min(start + CHUNK_SIZE, len(lines))
        chunk_lines = lines[start:end]
        content = "".join(chunk_lines)

        chunks.append({
            "content": content,
            "file_path": relative_path,
            "start_line": start + 1,
            "end_line": end,
            "language": _get_language(file_ext),
        })

        if end >= len(lines):
            break
        start += CHUNK_SIZE - OVERLAP
    return chunks

#Helper function to map file extensions to language names for syntax highlighting in LLM responses
def _get_language(ext: str) -> str:
    """Map file extension to language name."""
    lang_map = {
        ".py": "python", ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript", ".java": "java",
        ".cpp": "cpp", ".c": "c", ".go": "go", ".rs": "rust",
        ".rb": "ruby", ".php": "php", ".swift": "swift",
        ".kt": "kotlin", ".scala": "scala", ".h": "c",
        ".hpp": "cpp", ".cs": "csharp", ".vue": "vue",
        ".svelte": "svelte", ".html": "html", ".css": "css",
        ".scss": "scss", ".sql": "sql", ".sh": "bash",
        ".yaml": "yaml", ".yml": "yaml", ".json": "json",
        ".toml": "toml", ".md": "markdown", ".txt": "text",
    }
    return lang_map.get(ext, "text")
