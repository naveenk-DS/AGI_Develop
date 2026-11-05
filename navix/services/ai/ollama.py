import httpx, os
from loguru import logger
from dotenv import load_dotenv

load_dotenv(".env")
OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

async def chat(
    prompt: str,
    model: str = "qwen2.5:7b",
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

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA}/api/chat", json={
                "model": model,
                "messages": messages,
                "stream": False
            })
            r.raise_for_status()
            return r.json()["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama chat error ({model} at {OLLAMA}): {e}")
        return f"Could not reach Ollama model '{model}'. Make sure 'ollama serve' is running and you have run 'ollama pull {model}'."

async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text})
        r.raise_for_status()
        return r.json()["embedding"]


from fastapi.responses import StreamingResponse
import json

async def chat_stream(
    prompt: str,
    model: str = "qwen2.5:7b",
    system: str = None,
    history: list[dict] = None
):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{OLLAMA}/api/chat", json={
            "model": model,
            "messages": messages,
            "stream": True
        }) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue



async def preload_model(model: str = "qwen2.5:7b"):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(f"{OLLAMA}/api/generate", json={
                "model": model,
                "prompt": "hello",
                "stream": False
            })
        logger.info(f"Model preloaded: {model}")
    except Exception as e:
        logger.warning(f"Could not preload model: {e}")
