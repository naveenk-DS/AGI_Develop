from langchain_ollama import ChatOllama, OllamaEmbeddings

_llm_instance = None
_llm_model_name = None

def get_llm(model: str = "qwen2.5:7b", temperature: float = 0.7):
    global _llm_instance, _llm_model_name
    if _llm_instance is None or _llm_model_name != model:
        _llm_instance = ChatOllama(
            model=model,
            temperature=temperature,
            base_url="http://127.0.0.1:11434",
            num_gpu=1,
            num_thread=8,
            num_ctx=4096,
            repeat_penalty=1.1
        )
        _llm_model_name = model
    return _llm_instance

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