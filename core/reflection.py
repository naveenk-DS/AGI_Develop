from core.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

async def reflect_and_improve(question: str, initial_answer: str) -> str:
    try:
        llm = get_llm()

        reflection_prompt = f"""You are a critical reviewer. Review this answer and improve it.

Question: {question}
Initial Answer: {initial_answer}

Check for:
1. Is the answer accurate and complete?
2. Is it too long or too short?
3. Does it directly answer the question?
4. Is the tone natural and conversational?

If the answer is already good — return it exactly as is.
If it needs improvement — return only the improved version.
Return ONLY the final answer, nothing else. No explanations."""

        messages = [
            SystemMessage(content="You are an answer reviewer. Return only the improved answer."),
            HumanMessage(content=reflection_prompt)
        ]

        result = await llm.ainvoke(messages)
        improved = result.content.strip()

        if improved and len(improved) > 10:
            logger.info(f"Reflection improved answer: {len(initial_answer)} -> {len(improved)} chars")
            return improved
        return initial_answer

    except Exception as e:
        logger.warning(f"Reflection failed: {e}")
        return initial_answer


async def fact_check(statement: str) -> dict:
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content="You are a fact checker. Be brief and direct."),
            HumanMessage(content=(
                f"Is this statement accurate? Answer with: "
                f"ACCURATE, INACCURATE, or UNCERTAIN — then one sentence explanation.\n\n"
                f"Statement: {statement}"
            ))
        ]
        result = await llm.ainvoke(messages)
        text = result.content.strip()

        if "INACCURATE" in text.upper():
            verdict = "inaccurate"
        elif "UNCERTAIN" in text.upper():
            verdict = "uncertain"
        else:
            verdict = "accurate"

        return {"verdict": verdict, "explanation": text}
    except Exception as e:
        logger.warning(f"Fact check failed: {e}")
        return {"verdict": "unknown", "explanation": str(e)}