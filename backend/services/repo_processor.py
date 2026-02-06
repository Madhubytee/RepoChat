import os
import tempfile
import shutil
from typing import List
from git import Repo, GitCommandError

#files for repochat to ihnore when walking the repo and chunking files, this is to avoid unnecessary processing of files that are not relevant for code understanding and also to avoid very large files that can cause performance issues
IGNORE_DIRS = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    ".next", ".venv", "venv", "env", ".env", ".idea", ".vscode",
    "vendor", "target", "bin", "obj", ".cache", "coverage",
}

CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".h", ".hpp", ".cs", ".vue", ".svelte", ".html", ".css",
    ".scss", ".sql", ".sh", ".yaml", ".yml", ".json", ".toml",
    ".md", ".txt",
}

LOCK_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "composer.lock",
    "Gemfile.lock", "Cargo.lock",
}

MAX_FILE_SIZE = 500_000  #500KB - to avoid processing very large files that can cause performance issues


def clone_repo(github_url: str) -> str:
    """Clone a GitHub repo to a temp directory using shallow clone."""
    temp_dir = tempfile.mkdtemp(prefix="repochat_")
    try:
        Repo.clone_from(
            github_url,
            temp_dir,
            depth=1,
            single_branch=True,
        )
        return temp_dir
    except GitCommandError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if "not found" in str(e).lower() or "404" in str(e):
            raise ValueError(f"Repository not found: {github_url}")
        
        if "authentication" in str(e).lower() or "403" in str(e):
            raise ValueError(f"Repository is private or requires authentication: {github_url}")
        raise ValueError(f"Failed to clone repository: {e}")
    
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError(f"Unexpected error cloning repository: {e}")


def get_code_files(repo_path: str) -> List[str]:
    """Walk through directory and return code file paths, ignoring nonessential dirs."""
    code_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in LOCK_FILES:
                continue

            ext = os.path.splitext(file)[1].lower()
            if ext not in CODE_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)

            try:
                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            code_files.append(file_path)

    return code_files


def cleanup_repo(repo_path: str):
    """Remove the cloned repo directory."""
    shutil.rmtree(repo_path, ignore_errors=True)
