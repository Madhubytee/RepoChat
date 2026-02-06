# RepoChat

Chat with any GitHub repository using AI-powered RAG (Retrieval-Augmented Generation).

## How It Works

1. **Clone** - Fetches the repository using a shallow git clone
2. **Chunk** - Splits code files into ~50 line segments with overlap
3. **Embed** - Converts chunks to vectors using OpenAI's text-embedding-3-small
4. **Store** - Saves embeddings in ChromaDB for fast similarity search
5. **Chat** - Retrieves relevant code chunks and generates answers with GPT-4o

## Tech Stack

- **Backend**: FastAPI, ChromaDB, OpenAI API, GitPython
- **Frontend**: Next.js, TypeScript, Tailwind CSS, React Markdown

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/RepoChat.git
cd RepoChat
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env` with your OpenAI key:
```
OPENAI_API_KEY=your-openai-key
```

Start the server:
```bash
python -m uvicorn main:app --reload
```

Server runs at http://localhost:8000

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at http://localhost:3000

## Usage

1. Open http://localhost:3000
2. Paste a public GitHub repository URL (e.g., `https://github.com/facebook/react`)
3. Wait for processing (cloning → chunking → embedding)
4. Ask questions about the codebase

## Project Structure

```
RepoChat/
├── backend/
│   ├── main.py                 # FastAPI app and endpoints
│   ├── requirements.txt
│   └── services/
│       ├── repo_processor.py   # Git clone and file discovery
│       ├── code_chunker.py     # Split files into chunks
│       ├── vector_store.py     # ChromaDB operations
│       └── llm_service.py      # OpenAI chat completions
├── frontend/
│   └── src/
│       ├── app/page.tsx        # Main page
│       └── components/         # React components
├── .env.example
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/process-repo` | POST | Clone and index a GitHub repo |
| `/api/chat` | POST | Chat with indexed repo (streaming) |
| `/api/status/{session_id}` | GET | Check processing status |

## Limitations

- Only works with public GitHub repositories
- Large repos may take longer to process
- Requires OpenAI API key 
