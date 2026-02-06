import uuid
import asyncio
import re
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
from services.repo_processor import clone_repo, get_code_files, cleanup_repo
from services.code_chunker import chunk_code_file
from services.vector_store import create_collection, get_collection, add_chunks, search
from services.llm_service import generate_response_stream

app = FastAPI(title="RepoChat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}
class ProcessRepoRequest(BaseModel):
    github_url: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/process-repo")
async def process_repo(request: ProcessRepoRequest):
    session_id = str(uuid.uuid4()).replace("-", "")[:16]
    github_url = request.github_url.strip()

    #Validate the GitHub URL format ex: https://github.com/owner/repo
    github_pattern = r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
    if not re.match(github_pattern, github_url):
        raise HTTPException(status_code=400, detail="Please provide a valid GitHub URL (https://github.com/owner/repo)")
    sessions[session_id] = {"status": "cloning", "files_processed": 0}

    repo_path = None
    try:
        #Clones the repo
        repo_path = await asyncio.to_thread(clone_repo, github_url)
        sessions[session_id]["status"] = "processing"

        code_files = await asyncio.to_thread(get_code_files, repo_path)

        if not code_files:
            raise HTTPException(status_code=400, detail="No code files found in repository")

        #Chunk all files
        all_chunks = []
        for file_path in code_files:
            chunks = chunk_code_file(file_path, repo_path)
            all_chunks.extend(chunks)

        sessions[session_id]["status"] = "embedding"

        #Creates a collection and store embeddings
        collection = create_collection(session_id)

        await asyncio.to_thread(add_chunks, collection, all_chunks)

        sessions[session_id] = {
            "status": "ready",
            "files_processed": len(code_files),
            "total_chunks": len(all_chunks),
            "repo_url": github_url,
        }
        return {
            "session_id": session_id,
            "files_processed": len(code_files),
            "total_chunks": len(all_chunks),
        }

    except ValueError as e:
        sessions[session_id]["status"] = "error"
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        sessions[session_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"Error processing repository: {e}")
    finally:
        if repo_path:
            cleanup_repo(repo_path)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if session_id not in sessions or sessions[session_id]["status"] != "ready":
        raise HTTPException(status_code=404, detail="Session not found or not ready")

    try:
        collection = get_collection(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session data not found")

    #Searches for relevant chunks
    context_chunks = await asyncio.to_thread(search, collection, message, 5)

    sources = list({chunk["file_path"] for chunk in context_chunks})

    async def stream_response():
        async for token in generate_response_stream(message, context_chunks):
            yield token
        #Sends sources as a final JSON 
        yield f"\n\n---SOURCES---\n" + "\n".join(sources)

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.get("/api/status/{session_id}")
def get_status(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]
