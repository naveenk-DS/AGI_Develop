from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from core.rag_chain import ingest_documents, get_rag_chain
from app.services.document_loader import load_document
from loguru import logger
from pathlib import Path

router = APIRouter(prefix="/rag", tags=["rag"])

class QueryRequest(BaseModel):
    question: str

class IngestPathRequest(BaseModel):
    file_path: str
    doc_name: str = None

class AdvancedQueryRequest(BaseModel):
    question: str

@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    count = ingest_documents([text], doc_name=file.filename)
    return {"status": "ok", "file": file.filename, "chunks_stored": count}

@router.post("/ingest-path")
async def ingest_from_path(body: IngestPathRequest):
    path = Path(body.file_path)
    if not path.exists():
        return {"error": f"File not found: {body.file_path}"}
    try:
        text = load_document(body.file_path)
        doc_name = body.doc_name or path.name
        count = ingest_documents([text], doc_name=doc_name)
        return {
            "status": "ok",
            "doc_name": doc_name,
            "chunks_stored": count
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/query")
async def query(body: QueryRequest):
    try:
        chain = get_rag_chain()
        result = chain.invoke({"query": body.question})
        answer = result["result"] if isinstance(result, dict) else str(result)
        return {"question": body.question, "answer": answer}
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return {"error": str(e)}

@router.post("/advanced")
async def advanced_query(body: AdvancedQueryRequest):
    try:
        from core.advanced_rag import advanced_rag_query
        result = await advanced_rag_query(body.question)
        return {"question": body.question, "answer": result}
    except Exception as e:
        logger.error(f"Advanced RAG error: {e}")
        return {"error": str(e)}