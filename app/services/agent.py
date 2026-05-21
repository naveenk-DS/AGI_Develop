from app.services.ollama import chat as ollama_chat
from app.services.qdrant import search
from app.services.ollama import embed
from loguru import logger

TOOLS = {
    "rag_search": "Search through ingested documents to answer questions about specific content",
    "direct_chat": "Answer general questions, have conversations, explain concepts",
    "summarise": "Summarise a topic or generate a report based on documents"
}

async def decide_tool(user_message: str) -> str:
    tool_descriptions = "\n".join([f"- {k}: {v}" for k, v in TOOLS.items()])

    decision_prompt = f"""You are a router. Your only job is to pick the right tool.

Available tools:
{tool_descriptions}

User message: "{user_message}"

Reply with ONLY the tool name — nothing else. No explanation. Just one of: rag_search, direct_chat, summarise"""

    decision = await ollama_chat(decision_prompt)
    decision = decision.strip().lower()

    # clean up in case model adds extra text
    for tool in TOOLS.keys():
        if tool in decision:
            return tool

    # default fallback
    return "direct_chat"

async def run_agent(
    user_message: str,
    session_id: str,
    history: list[dict] = None
) -> dict:
    # step 1 — decide which tool to use
    tool = await decide_tool(user_message)
    logger.info(f"Agent decision: {tool} for message: '{user_message[:50]}'")

    result = {
        "tool_used": tool,
        "question": user_message,
        "answer": "",
        "context_chunks": 0
    }

    if tool == "rag_search":
        # search documents first then answer
        question_embedding = await embed(user_message)
        chunks = search(question_embedding, top_k=3)

        if not chunks:
            result["answer"] = "I searched the documents but found nothing relevant. Try ingesting some documents first."
            return result

        context = "\n\n".join(chunks)
        prompt = f"""Use this context from the documents to answer the question.
If the answer is not in the context say "I could not find this in the documents."

Context:
{context}

Question: {user_message}"""

        result["answer"] = await ollama_chat(prompt)
        result["context_chunks"] = len(chunks)

    elif tool == "summarise":
        question_embedding = await embed(user_message)
        chunks = search(question_embedding, top_k=5)

        if chunks:
            context = "\n\n".join(chunks)
            prompt = f"""Based on these documents, create a clear summary.

Documents:
{context}

Request: {user_message}"""
        else:
            prompt = user_message

        result["answer"] = await ollama_chat(prompt)
        result["context_chunks"] = len(chunks) if chunks else 0

    else:
        # direct chat with history
        result["answer"] = await ollama_chat(
            prompt=user_message,
            system="You are a helpful AI assistant. Be concise and clear.",
            history=history or []
        )

    return result