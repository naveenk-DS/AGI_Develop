from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from qdrant_client import QdrantClient
# pyrefly: ignore [missing-import]
from rank_bm25 import BM25Okapi
from core.llm import get_llm, get_embeddings
from loguru import logger
import re

COLLECTION = "documents"
QDRANT_URL = "http://127.0.0.1:6333"

def get_vectorstore() -> QdrantVectorStore:
    client = QdrantClient(url=QDRANT_URL)
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION,
        embedding=get_embeddings()
    )

def keyword_search(query: str, docs: list[Document], top_k: int = 5) -> list[Document]:
    if not docs:
        return []
    try:
        tokenized = [d.page_content.lower().split() for d in docs]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
        ranked = sorted(zip(scores, docs), reverse=True)
        return [d for _, d in ranked[:top_k]]
    except Exception as e:
        logger.warning(f"BM25 error: {e}")
        return docs[:top_k]

async def expand_query(query: str) -> list[str]:
    try:
        llm = get_llm()
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content="Generate 3 alternative search queries. Return only the queries, one per line, nothing else."),
            HumanMessage(content=f"Original query: {query}")
        ]
        result = await llm.ainvoke(messages)
        lines = [l.strip() for l in result.content.strip().split("\n") if l.strip()]
        queries = [query] + lines[:3]
        logger.info(f"Query expanded: {len(queries)} variants")
        return queries
    except Exception as e:
        logger.warning(f"Query expansion failed: {e}")
        return [query]

async def rerank(query: str, docs: list[Document]) -> list[Document]:
    if not docs or len(docs) <= 1:
        return docs
    try:
        llm = get_llm()
        from langchain_core.messages import HumanMessage, SystemMessage

        docs_text = "\n".join([
            f"[{i}] {d.page_content[:200]}"
            for i, d in enumerate(docs)
        ])
        messages = [
            SystemMessage(content="Rank documents by relevance to query. Return only comma-separated indices like: 2,0,3,1"),
            HumanMessage(content=f"Query: {query}\n\nDocuments:\n{docs_text}")
        ]
        result = await llm.ainvoke(messages)
        indices_str = re.findall(r'\d+', result.content)
        indices = [int(i) for i in indices_str if int(i) < len(docs)]

        # add any missing indices
        all_idx = list(range(len(docs)))
        for i in all_idx:
            if i not in indices:
                indices.append(i)

        reranked = [docs[i] for i in indices]
        logger.info(f"Reranked {len(reranked)} documents")
        return reranked
    except Exception as e:
        logger.warning(f"Reranking failed: {e}")
        return docs

async def hybrid_search(query: str, top_k: int = 5) -> list[Document]:
    try:
        vectorstore = get_vectorstore()

        # vector search
        vector_docs = vectorstore.similarity_search(query, k=top_k * 2)

        # keyword search on vector results
        keyword_docs = keyword_search(query, vector_docs, top_k=top_k)

        # combine — deduplicate by content
        seen = set()
        combined = []
        for doc in keyword_docs + vector_docs:
            key = doc.page_content[:100]
            if key not in seen:
                seen.add(key)
                combined.append(doc)

        return combined[:top_k]
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        return []

async def advanced_rag_query(question: str) -> str:
    try:
        # expand query
        queries = await expand_query(question)

        # search with all query variants
        all_docs = []
        seen = set()
        for q in queries:
            docs = await hybrid_search(q, top_k=3)
            for doc in docs:
                key = doc.page_content[:100]
                if key not in seen:
                    seen.add(key)
                    all_docs.append(doc)

        if not all_docs:
            return "I could not find relevant information in the documents."

        # rerank
        reranked = await rerank(question, all_docs[:10])

        # build context
        context = "\n\n".join([d.page_content for d in reranked[:4]])

        # generate answer
        llm = get_llm()
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=(
                "You are NAVIX. Answer using the context provided. "
                "Keep answer under 3 sentences. Be direct and natural."
            )),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}")
        ]
        result = await llm.ainvoke(messages)
        return result.content.strip()

    except Exception as e:
        logger.error(f"Advanced RAG error: {e}")
        return "Could not search documents right now."