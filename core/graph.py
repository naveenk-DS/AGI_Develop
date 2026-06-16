from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from core.llm import get_llm
from core.rag_chain import get_rag_chain
from core.emotion import detect_emotion, get_emotional_prefix
from loguru import logger
import operator

# ── OODA System Prompt ────────────────────────────────────────────────────────
OODA_SYSTEM = """You are NAVIX, Naveen's personal AI operating system.

Core Principles:
1. Voice First — keep responses concise, speak naturally
2. Intent Over Commands — understand what Naveen wants, not just what he says
3. Autonomous Execution — break goals into tasks, execute, recover from failures
4. Memory — remember preferences, projects, decisions, goals

You can act as:
- Coding assistant
- Research assistant  
- Browser operator
- Task manager
- Planner
- Personal knowledge assistant

For every request follow:
Goal → Plan → Execute → Verify → Complete

When stuck:
- Diagnose the blocker
- Attempt recovery
- If still blocked ask Naveen one clear question

Output style for voice:
- Understanding: what you understood
- Action: what you did
- Status: done or not
- Next: what comes next

Keep all voice responses under 3 sentences.
Never use bullet points or markdown when speaking.
Talk like a close friend who is also highly capable."""


# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    user_input:       str
    understood:       str        # what NAVIX understood
    plan:             list       # list of steps
    current_step:     int        # which step we are on
    tool:             str        # which tool to use
    tool_result:      str        # result from tool
    verified:         bool       # did Naveen confirm it worked
    response:         str        # final response to speak
    emotion:          str        # detected emotion
    personal_context: str        # personal memory context
    messages:         Annotated[list, operator.add]


# ── Node 1 — Input ────────────────────────────────────────────────────────────
def input_node(state: AgentState) -> AgentState:
    """Receive voice input and detect emotion."""
    from core.emotion import detect_emotion
    emotion = detect_emotion(state["user_input"])
    logger.info(f"Input received — emotion: {emotion}")
    return {**state, "emotion": emotion, "current_step": 0}


# ── Node 2 — Understand ───────────────────────────────────────────────────────
async def understand_node(state: AgentState) -> AgentState:
    """Understand what Naveen actually wants — intent over literal words."""
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=OODA_SYSTEM),
            HumanMessage(content=(
                f"Naveen said: '{state['user_input']}'\n\n"
                f"Personal context: {state.get('personal_context', '')}\n\n"
                "In one sentence — what does Naveen actually want to achieve? "
                "Be specific. Example: 'Naveen wants to know current weather in Chennai' "
                "not just 'weather question'."
            ))
        ]
        result = await llm.ainvoke(messages)
        understood = result.content.strip()
        logger.info(f"Understood: {understood}")
        return {**state, "understood": understood}
    except Exception as e:
        logger.error(f"Understand error: {e}")
        return {**state, "understood": state["user_input"]}


# ── Node 3 — Plan ─────────────────────────────────────────────────────────────
async def plan_node(state: AgentState) -> AgentState:
    """Break the goal into steps and pick the right tool."""
    try:
        llm = get_llm()
        user_input = state["user_input"].lower()

        # Fast route for simple commands — no LLM needed
        if any(w in user_input for w in [
            "open", "play", "search", "youtube", "google",
            "chrome", "website", "news", "wikipedia"
        ]):
            return {**state, "tool": "browser", "plan": ["open browser", "execute command"]}

        if any(w in user_input for w in [
            "click", "type", "press", "volume", "screenshot",
            "minimize", "maximize", "scroll", "keyboard"
        ]):
            return {**state, "tool": "pc", "plan": ["execute pc command"]}

        if any(w in user_input for w in [
            "remember", "my friend", "my family", "favourite",
            "birthday", "save this", "don't forget", "recall"
        ]):
            return {**state, "tool": "memory", "plan": ["save or recall memory"]}

        if any(w in user_input for w in [
            "document", "file", "pdf", "what does it say",
            "in the document", "search my files"
        ]):
            return {**state, "tool": "rag", "plan": ["search documents"]}

        if any(w in user_input for w in [
            "write code", "create function", "build", "fix this code",
            "debug", "python script", "program"
        ]):
            return {**state, "tool": "code", "plan": ["understand requirement", "write code", "verify"]}

        if any(w in user_input for w in [
            "research", "find out", "investigate", "deep dive",
            "explain everything about", "tell me all about"
        ]):
            return {**state, "tool": "research", "plan": ["research topic", "summarize", "respond"]}

        # LLM decides for everything else
        messages = [
            SystemMessage(content=OODA_SYSTEM),
            HumanMessage(content=(
                f"Goal: {state['understood']}\n\n"
                "Which tool should handle this?\n"
                "Options: chat, rag, browser, pc, memory, code, research\n"
                "Reply with ONLY the tool name. Nothing else."
            ))
        ]
        result = await llm.ainvoke(messages)
        tool = result.content.strip().lower()

        # validate tool name
        valid_tools = ["chat", "rag", "browser", "pc", "memory", "code", "research"]
        if tool not in valid_tools:
            tool = "chat"

        logger.info(f"Plan — tool: {tool}")
        return {**state, "tool": tool, "plan": ["execute", "verify", "respond"]}

    except Exception as e:
        logger.error(f"Plan error: {e}")
        return {**state, "tool": "chat", "plan": ["chat"]}


# ── Node 4 — Router ───────────────────────────────────────────────────────────
def router_node(state: AgentState) -> str:
    """Route to correct tool node."""
    tool = state.get("tool", "chat")
    logger.info(f"Routing to: {tool}")
    return tool


# ── Node 5a — Chat ────────────────────────────────────────────────────────────
async def chat_node(state: AgentState) -> AgentState:
    try:
        llm = get_llm()
        emotional_prefix = get_emotional_prefix(state["user_input"])
        personal_context = state.get("personal_context", "")

        messages = [
            SystemMessage(content=f"{OODA_SYSTEM}\n\n{personal_context}"),
            HumanMessage(content=state["user_input"])
        ]
        result = await llm.ainvoke(messages)
        response = emotional_prefix + result.content.strip()
        logger.info("Chat node complete")
        return {**state, "tool_result": response, "response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {**state, "response": "Sorry something went wrong."}


# ── Node 5b — RAG ─────────────────────────────────────────────────────────────
async def rag_node(state: AgentState) -> AgentState:
    try:
        chain = get_rag_chain()
        result = chain.invoke({"query": state["user_input"]})
        response = result["result"] if isinstance(result, dict) else str(result)
        logger.info("RAG node complete")
        return {**state, "tool_result": response, "response": response}
    except Exception as e:
        logger.error(f"RAG error: {e}")
        return {**state, "response": "Could not find that in documents."}


# ── Node 5c — Browser ─────────────────────────────────────────────────────────
async def browser_node(state: AgentState) -> AgentState:
    try:
        from app.services.command_parser import execute_browser_command
        result = await execute_browser_command(state["user_input"])
        response = result or "Done."
        logger.info(f"Browser node complete: {response}")
        return {**state, "tool_result": response, "response": response}
    except Exception as e:
        logger.error(f"Browser error: {e}")
        return {**state, "response": f"Browser error: {e}"}


# ── Node 5d — PC ─────────────────────────────────────────────────────────────
async def pc_node(state: AgentState) -> AgentState:
    try:
        from app.services.pc_command_parser import execute_pc_command
        result = await execute_pc_command(state["user_input"])
        response = result or "Done."
        logger.info(f"PC node complete: {response}")
        return {**state, "tool_result": response, "response": response}
    except Exception as e:
        logger.error(f"PC error: {e}")
        return {**state, "response": f"PC error: {e}"}


# ── Node 5e — Memory ──────────────────────────────────────────────────────────
async def memory_node(state: AgentState) -> AgentState:
    try:
        from app.services.personal_memory import (
            add_family, add_friend, set_favourite,
            add_birthday, add_memory
        )
        import re
        text = state["user_input"].lower()

        friend_match = re.search(r"(\w+) is my friend", text)
        if friend_match:
            result = await add_friend(friend_match.group(1))
            return {**state, "tool_result": result, "response": result}

        family_match = re.search(r"(\w+) is my (\w+)", text)
        if family_match:
            result = await add_family(
                family_match.group(1),
                family_match.group(2)
            )
            return {**state, "tool_result": result, "response": result}

        fav_match = re.search(r"my favourite (\w+) is (.+)", text)
        if fav_match:
            result = await set_favourite(
                fav_match.group(1),
                fav_match.group(2)
            )
            return {**state, "tool_result": result, "response": result}

        await add_memory(state["user_input"])
        response = "Got it Naveen, I will remember that."
        return {**state, "tool_result": response, "response": response}
    except Exception as e:
        logger.error(f"Memory error: {e}")
        return {**state, "response": "Could not save that memory."}


# ── Node 5f — Code ───────────────────────────────────────────────────────────
async def code_node(state: AgentState) -> AgentState:
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=(
                f"{OODA_SYSTEM}\n\n"
                "You are in coding mode. "
                "Write clean production grade Python code. "
                "No explanations unless asked. "
                "Just the code with brief comments."
            )),
            HumanMessage(content=state["user_input"])
        ]
        result = await llm.ainvoke(messages)
        response = result.content.strip()
        logger.info("Code node complete")
        return {**state, "tool_result": response, "response": response}
    except Exception as e:
        logger.error(f"Code error: {e}")
        return {**state, "response": "Could not write that code."}


# ── Node 5g — Research ───────────────────────────────────────────────────────
async def research_node(state: AgentState) -> AgentState:
    try:
        import asyncio
        from core.crew import get_research_crew
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            get_research_crew,
            state["user_input"]
        )
        logger.info("Research node complete")
        return {**state, "tool_result": result, "response": result}
    except Exception as e:
        logger.error(f"Research error: {e}")
        return {**state, "response": "Could not research that right now."}


# ── Node 6 — Verify ──────────────────────────────────────────────────────────
async def verify_node(state: AgentState) -> AgentState:
    """Ask Naveen by voice if it worked."""
    try:
        from app.services.voice.speaker import speak
        from app.services.voice.listener import listen_once

        tool = state.get("tool", "chat")

        # only verify for actions — not for chat or memory
        if tool in ["chat", "memory", "rag"]:
            return {**state, "verified": True}

        # ask Naveen
        speak("Did that work okay?")
        answer = listen_once(duration=5)

        if answer and any(w in answer.lower() for w in [
            "yes", "yeah", "yep", "good", "great",
            "works", "working", "perfect", "okay", "ok"
        ]):
            verified = True
            logger.info("Verified: yes")
        else:
            verified = False
            logger.info(f"Verified: no — Naveen said: {answer}")

        return {**state, "verified": verified}
    except Exception as e:
        logger.error(f"Verify error: {e}")
        return {**state, "verified": True}


# ── Node 7 — Respond ─────────────────────────────────────────────────────────
async def respond_node(state: AgentState) -> AgentState:
    """Build final response to speak to Naveen."""
    try:
        verified = state.get("verified", True)
        tool_result = state.get("tool_result", "")
        tool = state.get("tool", "chat")

        if not verified:
            # not verified — tell Naveen and ask what to do
            llm = get_llm()
            messages = [
                SystemMessage(content=OODA_SYSTEM),
                HumanMessage(content=(
                    f"The action failed or did not work. Tool used: {tool}. "
                    f"Result was: {tool_result}. "
                    "Tell Naveen briefly what happened and ask what he wants to do next. "
                    "1-2 sentences."
                ))
            ]
            result = await llm.ainvoke(messages)
            response = result.content.strip()
        else:
            # verified — response already set by tool node
            response = state.get("response", "Done.")

        logger.info(f"Final response: {response[:60]}")
        return {**state, "response": response}
    except Exception as e:
        logger.error(f"Respond error: {e}")
        return {**state, "response": "Done."}


# ── Build Graph ───────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    # ── Add all nodes ─────────────────────────────────────────────────────────
    graph.add_node("input",    input_node)
    graph.add_node("understand", understand_node)
    graph.add_node("plan",     plan_node)
    graph.add_node("chat",     chat_node)
    graph.add_node("rag",      rag_node)
    graph.add_node("browser",  browser_node)
    graph.add_node("pc",       pc_node)
    graph.add_node("memory",   memory_node)
    graph.add_node("code",     code_node)
    graph.add_node("research", research_node)
    graph.add_node("verify",   verify_node)
    graph.add_node("respond",  respond_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("input")

    # ── Edges ─────────────────────────────────────────────────────────────────
    # START → input → understand → plan
    graph.add_edge("input",      "understand")
    graph.add_edge("understand", "plan")

    # plan → router → tool nodes
    graph.add_conditional_edges(
        "plan",
        router_node,
        {
            "chat":     "chat",
            "rag":      "rag",
            "browser":  "browser",
            "pc":       "pc",
            "memory":   "memory",
            "code":     "code",
            "research": "research",
        }
    )

    # all tool nodes → verify
    graph.add_edge("chat",     "verify")
    graph.add_edge("rag",      "verify")
    graph.add_edge("browser",  "verify")
    graph.add_edge("pc",       "verify")
    graph.add_edge("memory",   "verify")
    graph.add_edge("code",     "verify")
    graph.add_edge("research", "verify")

    # verify → respond → END
    graph.add_edge("verify",  "respond")
    graph.add_edge("respond", END)

    return graph.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
        logger.info("LangGraph compiled — START→input→understand→plan→[tool]→verify→respond→END")
    return _graph