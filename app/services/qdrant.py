from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from pathlib import Path
import os, uuid

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / "config" / ".env")

client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))

COLLECTION = "documents"
VECTOR_SIZE = 768  # nomic-embed-text output size

def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"Created collection: {COLLECTION}")

def save_chunks(chunks: list[dict]) -> int:
    ensure_collection()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=chunk["embedding"],
            payload={"text": chunk["text"], "doc_name": chunk["doc_name"]}
        )
        for chunk in chunks
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)

def search(embedding: list[float], top_k: int = 3) -> list[str]:
    ensure_collection()
    response = client.query_points(
        collection_name=COLLECTION,
        query=embedding,
        limit=top_k
    )
    return [r.payload["text"] for r in response.points]
