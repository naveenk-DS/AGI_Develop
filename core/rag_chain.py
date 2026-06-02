from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from core.llm import get_llm, get_embeddings
from loguru import logger

COLLECTION = "documents"
QDRANT_URL = "http://127.0.0.1:6333"

def get_vectorstore() -> QdrantVectorStore:
    client = QdrantClient(url=QDRANT_URL)
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION,
        embedding=get_embeddings()
    )

def _format_docs(docs: list) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain():
    """Return an LCEL chain that accepts {"query": str} and returns a str answer."""
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    prompt = PromptTemplate(
        template="""You are NAVIX, a helpful AI assistant.
Use the context below to answer the question.
If the answer is not in the context, say "I don't know based on the documents."
Keep answer under 3 sentences.

Context: {context}

Question: {question}

Answer:""",
        input_variables=["context", "question"]
    )
    # LCEL pipeline: accepts {"query": ...} dict, returns plain string
    chain = (
        {
            "context": RunnableLambda(lambda x: x["query"]) | retriever | _format_docs,
            "question": RunnableLambda(lambda x: x["query"])
        }
        | prompt
        | get_llm()
        | StrOutputParser()
    )
    return chain

def ingest_documents(texts: list[str], doc_name: str = "unknown") -> int:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50
    )
    docs = []
    for text in texts:
        chunks = splitter.split_text(text)
        for chunk in chunks:
            docs.append(Document(
                page_content=chunk,
                metadata={"doc_name": doc_name}
            ))
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs)
    logger.info(f"Ingested {len(docs)} chunks from {doc_name}")
    return len(docs)