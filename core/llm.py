from langchain_ollama import ChatOllama, OllamaEmbeddings
from functools import lru_cache

@lru_cache(maxsize=1)
def get_llm(model: str = "llama3.1", temperature: float = 0.7):
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url="http://127.0.0.1:11434"
    )

@lru_cache(maxsize=1)
def get_embeddings():
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://127.0.0.1:11434"
    )