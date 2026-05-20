
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.services.ollama import embed, chat
from app.services.qdrant import save_chunks, search
from loguru import logger

router = APIRouter(prefix="/rag", tags=["rag"])

def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return chunks

@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    chunks = chunk_text(text)
    logger.info(f"Ingesting {file.filename} — {len(chunks)} chunks")

    embedded_chunks = []
    for i, chunk in enumerate(chunks):
        embedding = await embed(chunk)
        embedded_chunks.append({
            "text": chunk,
            "embedding": embedding,
            "doc_name": file.filename
        })
        logger.info(f"  Embedded chunk {i+1}/{len(chunks)}")

    count = save_chunks(embedded_chunks)
    return {"status": "ok", "file": file.filename, "chunks_stored": count}

class QueryRequest(BaseModel):
    question: str

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
        "chunks_used": len(relevant_chunks)
    }

class IngestPathRequest(BaseModel):
    file_path: str
    doc_name: str = None

@router.post("/ingest-path")
async def ingest_from_path(body: IngestPathRequest):
    from pathlib import Path

    path = Path(body.file_path)
    if not path.exists():
        return {"error": f"File not found: {body.file_path}"}

    text = path.read_text(encoding="utf-8", errors="ignore")
    doc_name = body.doc_name or path.name
    chunks = chunk_text(text)

    embedded_chunks = []
    for i, chunk in enumerate(chunks):
        embedding = await embed(chunk)
        embedded_chunks.append({
            "text": chunk,
            "embedding": embedding,
            "doc_name": doc_name
        })

    count = save_chunks(embedded_chunks)
    return {"status": "ok", "doc_name": doc_name, "chunks_stored": count}