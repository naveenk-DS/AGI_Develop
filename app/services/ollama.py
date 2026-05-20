import httpx, os
from loguru import logger
from dotenv import load_dotenv

load_dotenv("config/.env")
OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

async def chat(
    prompt: str,
    model: str = "llama3",
    system: str = None,
    history: list[dict] = None
) -> str:
    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    # add previous conversation history
    if history:
        messages.extend(history)

    # add current user message
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA}/api/chat", json={
            "model": model,
            "messages": messages,
            "stream": False
        })
        r.raise_for_status()
        return r.json()["message"]["content"]
async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text})
        r.raise_for_status()
        return r.json()["embedding"]