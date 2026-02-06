import os
from typing import List

import chromadb
from chromadb.config import Settings
from openai import OpenAI

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_data")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


_chroma_client = None
_openai_client = None


def _get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma_client


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def create_collection(session_id: str):
    #Creates a new ChromaDB collection for a session.
    client = _get_chroma_client()
    #Deletes the existing collection if it exists
    try:
        client.delete_collection(name=session_id)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=session_id,
        metadata={"hnsw:space": "cosine"},
    )
def get_collection(session_id: str):
    #Get an existing collection by session_id.
    client = _get_chroma_client()
    return client.get_collection(name=session_id)


def _get_embeddings(texts: List[str]) -> List[List[float]]:
    #Generate embeddings using OpenAI.
    client = _get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def add_chunks(collection, chunks: List[dict]):
   #Add code chunks to the vector store in batches.
    if not chunks:
        return

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        documents = []
        metadatas = []
        ids = []

        for j, chunk in enumerate(batch):
            doc = f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})\n\n{chunk['content']}"
            documents.append(doc)
            metadatas.append({
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "language": chunk.get("language", "text"),
            })
            ids.append(f"chunk_{i + j}")

        embeddings = _get_embeddings(documents)

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

def search(collection, query: str, n_results: int = 5) -> List[dict]:
    """Search the vector store for relevant chunks."""
    query_embedding = _get_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    search_results = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            search_results.append({
                "content": doc,
                "file_path": meta["file_path"],
                "start_line": meta["start_line"],
                "end_line": meta["end_line"],
                "language": meta.get("language", "text"),
                "relevance_score": 1 - dist,  #cosine distance to similarity
            })

    return search_results
