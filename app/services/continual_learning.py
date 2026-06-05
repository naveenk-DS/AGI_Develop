import asyncio
from pathlib import Path
from loguru import logger
from app.services.document_loader import load_document
from core.rag_chain import ingest_documents
from app.services.knowledge_graph import add_document_to_graph

WATCH_DIR = Path("F:/naveen/AGI_Start/watch")
PROCESSED_DIR = WATCH_DIR / "processed"
LEARNING_LOG = Path("F:/naveen/AGI_Start/logs/learning.log")

_learning = False

async def process_new_document(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        logger.info(f"Learning from: {path.name}")

        # load text
        text = load_document(file_path)
        if not text or len(text.strip()) < 50:
            return {"error": "Document too short or empty"}

        # add to RAG vector store
        chunks = ingest_documents([text], doc_name=path.name)
        logger.info(f"RAG updated: {chunks} chunks from {path.name}")

        # add to knowledge graph
        entities, relations = await add_document_to_graph(text[:2000], path.name)
        logger.info(f"Graph updated: {entities} entities, {relations} relations")

        # log learning
        LEARNING_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LEARNING_LOG, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"{datetime.now().isoformat()} | {path.name} | chunks:{chunks} entities:{entities}\n")

        return {
            "status": "learned",
            "file": path.name,
            "chunks": chunks,
            "entities": entities,
            "relations": relations
        }
    except Exception as e:
        logger.error(f"Learning error for {file_path}: {e}")
        return {"error": str(e)}

async def watch_and_learn():
    global _learning
    _learning = True
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Continual learning started — watching {WATCH_DIR}")
    processed = set()

    while _learning:
        try:
            for ext in ["*.txt", "*.pdf", "*.docx", "*.csv", "*.md"]:
                for file in WATCH_DIR.glob(ext):
                    if file.name not in processed:
                        logger.info(f"New file detected: {file.name}")
                        result = await process_new_document(str(file))

                        if result.get("status") == "learned":
                            # move to processed
                            dest = PROCESSED_DIR / file.name
                            file.rename(dest)
                            processed.add(file.name)
                            logger.info(f"Processed and moved: {file.name}")
                        else:
                            logger.warning(f"Could not learn from {file.name}: {result}")
        except Exception as e:
            logger.error(f"Watch loop error: {e}")

        await asyncio.sleep(10)

def stop_learning():
    global _learning
    _learning = False
    logger.info("Continual learning stopped")