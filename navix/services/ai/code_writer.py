import re
from pathlib import Path
from datetime import datetime
from loguru import logger
from core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

OUTPUT_DIR = Path("C:/Users/Naveen/AGI_Develop/generated_code")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CODE_SYSTEM = (
    "You are a Python code generator. "
    "Write clean, working, production-quality code for the request. "
    "Output ONLY the code inside a single python code block. "
    "No explanations before or after. Include brief inline comments only where genuinely useful."
)

def _extract_filename(request: str) -> str:
    """Guess a reasonable filename from the request, fallback to timestamp."""
    match = re.search(r"(?:called|named|as)\s+([a-zA-Z0-9_]+)", request.lower())
    if match:
        name = match.group(1)
    else:
        words = re.findall(r"[a-zA-Z]+", request.lower())
        meaningful = [w for w in words if w not in (
            "write", "create", "make", "build", "a", "the", "simple", "code", "python", "for", "me"
        )]
        name = "_".join(meaningful[:3]) if meaningful else "script"
    return f"{name}.py"

def _extract_code_block(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

async def write_code_to_file(request: str) -> str:
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=CODE_SYSTEM),
            HumanMessage(content=request)
        ]
        result = await llm.ainvoke(messages)
        code = _extract_code_block(result.content)

        if not code or len(code) < 5:
            return "I couldn't generate working code for that. Can you describe it differently?"

        filename = _extract_filename(request)
        filepath = OUTPUT_DIR / filename

        if filepath.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            filepath = OUTPUT_DIR / f"{filepath.stem}_{timestamp}{filepath.suffix}"

        filepath.write_text(code, encoding="utf-8")
        logger.info(f"Code written: {filepath}")

        return f"Done. I saved it as {filepath.name} in your generated code folder."

    except Exception as e:
        logger.error(f"Code writer error: {e}")
        return "Something went wrong writing that code."