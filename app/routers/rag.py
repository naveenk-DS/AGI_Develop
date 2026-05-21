from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ollama import embed, chat
from app.services.qdrant import save_chunks, search
from loguru import logger
from app.services.document_loader import load_document, get_supported_extensions


router = APIRouter(prefix="/rag", tags=["rag"])


def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + size])
        chunks.append(chunk)
        i += size - overlap
    return chunks


# ── Models ────────────────────────────────────────────────────────────────────

class IngestPathRequest(BaseModel):
    file_path: str
    doc_name: str = None


class QueryRequest(BaseModel):
    question: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/ingest-path")
async def ingest_from_path(body: IngestPathRequest):
    from pathlib import Path

    path = Path(body.file_path)
    if not path.exists():
        return {"error": f"File not found: {body.file_path}"}

    suffix = path.suffix.lower()
    if suffix not in get_supported_extensions():
        return {"error": f"Unsupported file type: {suffix}. Supported: {get_supported_extensions()}"}

    try:
        text = load_document(body.file_path)
    except Exception as e:
        return {"error": f"Could not read file: {str(e)}"}

    if not text.strip():
        return {"error": "File is empty or could not be read"}

    doc_name = body.doc_name or path.name
    chunks = chunk_text(text)
    logger.info(f"Ingesting {doc_name} — {len(chunks)} chunks from {suffix} file")

    embedded_chunks = []
    for chunk in chunks:
        embedding = await embed(chunk)
        embedded_chunks.append({
            "text": chunk,
            "embedding": embedding,
            "doc_name": doc_name,
        })

    count = save_chunks(embedded_chunks)
    return {
        "status": "ok",
        "doc_name": doc_name,
        "file_type": suffix,
        "chunks_stored": count,
        "total_chars": len(text),
    }


@router.post("/query")
async def query(body: QueryRequest):
    question_embedding = await embed(body.question)
    relevant_chunks = search(question_embedding, top_k=3)

    context = "\n\n".join(relevant_chunks)
    prompt = f"""Use the following context to answer the question.
If the answer is not in the context, say "I don't know based on the documents."

Context:
{context}

Question: {body.question}"""

    answer = await chat(prompt)
    return {
        "question": body.question,
        "answer": answer,
        "chunks_used": len(relevant_chunks),
    }