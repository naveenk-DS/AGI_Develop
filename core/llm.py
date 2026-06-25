from langchain_ollama import ChatOllama, OllamaEmbeddings

def get_llm(model: str = "qwen2.5:7b", temperature: float = 0.7):
    """
    Return a ChatOllama instance.

    WHY not cached?
    ChatOllama (via langchain-ollama / httpx) binds its async connection pool
    to the event loop that first triggers an async call. On Windows,
    asyncio.run() creates a new loop each time, so a cached instance becomes
    stale and causes ainvoke() to hang indefinitely on the old loop's pool.
    Construction cost is negligible; the real I/O cost is the Ollama HTTP call.
    """
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url="http://127.0.0.1:11434",
        num_gpu=1,
        num_thread=8,
        num_ctx=4096,
        repeat_penalty=1.1
    )

def get_embeddings():
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://127.0.0.1:11434"
    )

def get_personality_llm():
    return ChatOllama(
        model="navix-personality",
        temperature=0.85,
        base_url="http://127.0.0.1:11434",
        num_gpu=1
    )