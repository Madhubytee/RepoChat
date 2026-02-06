import os
from typing import List, AsyncGenerator

from openai import OpenAI, AsyncOpenAI


MODEL = "gpt-4o"
MAX_TOKENS = 4096


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _get_async_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _build_prompt(query: str, context_chunks: List[dict]) -> str:
    #Build a prompt with code context for the LLM.
    formatted_chunks = []
    for i, chunk in enumerate(context_chunks, 1):
        formatted_chunks.append(
            f"--- Source {i}: {chunk['file_path']} "
            f"(lines {chunk['start_line']}-{chunk['end_line']}) ---\n"
            f"```{chunk.get('language', '')}\n{chunk['content']}\n```"
        )

    context = "\n\n".join(formatted_chunks)

    return f"""You are a knowledgeable code assistant. Answer the question using ONLY the provided code context from the repository. If the answer cannot be determined from the context, say so clearly.

FORMATTING RULES (important):
- Use proper Markdown formatting for readability
- Use headings (##, ###) to organize sections
- Use bullet points or numbered lists for multiple items
- Use **bold** for emphasis on key terms
- Use `inline code` for file names, function names, variables
- Use fenced code blocks with language tags for code snippets:
  ```javascript
  // code here
  ```
- Keep paragraphs short and well-spaced
- Reference files as `filename.ext:line_number` format

Code Context:
{context}

Question: {query}

Provide a well-formatted, organized answer with clear structure and specific code references."""


def generate_response(query: str, context_chunks: List[dict]) -> str:
    #Generate a response using OpenAI.
    client = _get_client()
    prompt = _build_prompt(query, context_chunks)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content or ""


async def generate_response_stream(
    query: str, context_chunks: List[dict]
) -> AsyncGenerator[str, None]:
    #Stream a response using OpenAI.
    client = _get_async_client()
    prompt = _build_prompt(query, context_chunks)

    stream = await client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
