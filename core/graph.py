from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from core.llm import get_llm, get_embeddings
from core.rag_chain import get_rag_chain
from core.emotion import detect_emotion, get_emotional_prefix
from app.services.personal_memory import get_context_for_ai
from loguru import logger
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    emotion: str
    tool: str
    response: str
    personal_context: str

def router_node(state: AgentState) -> AgentState:
    user_input = state["user_input"].lower()
    emotion = detect_emotion(state["user_input"])

    # smart routing
    if any(w in user_input for w in [
        "document", "file", "pdf", "what does", "according to",
        "in the document", "search documents", "find in"
    ]):
        tool = "rag"
    elif any(w in user_input for w in [
        "open", "search", "youtube", "google", "news",
        "wikipedia", "browser", "website", "play", "click"
    ]):
        tool = "browser"
    elif any(w in user_input for w in [
        "type", "press", "scroll", "screenshot", "volume",
        "minimize", "maximize", "window", "keyboard"
    ]):
        tool = "pc"
    elif any(w in user_input for w in [
        "remember", "my favourite", "my friend", "my family",
        "birthday", "save this", "don't forget", "i feel",
        "my goal", "my mood"
    ]):
        tool = "memory"
    else:
        tool = "chat"

    logger.info(f"Router → tool: {tool}, emotion: {emotion}")
    return {**state, "tool": tool, "emotion": emotion}


async def rag_node(state: AgentState) -> AgentState:
    try:
        from app.services.world_model import record_interaction
        from core.advanced_rag import advanced_rag_query
        from app.services.knowledge_graph import graph_search

        # advanced RAG with hybrid search + reranking
        vector_answer = await advanced_rag_query(state["user_input"])

        # graph RAG
        graph_context = await graph_search(state["user_input"])

        if graph_context and "could not" not in vector_answer.lower():
            llm = get_llm()
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content="Combine both answers into one clear response under 3 sentences."),
                HumanMessage(content=(
                    f"Question: {state['user_input']}\n"
                    f"Answer 1: {vector_answer}\n"
                    f"Graph context: {graph_context}\n"
                    f"Combined answer:"
                ))
            ]
            combined = await llm.ainvoke(messages)
            response = combined.content.strip()
        else:
            response = vector_answer

        await record_interaction(state["user_input"], "rag")
        return {**state, "response": response}
    except Exception as e:
        logger.error(f"RAG error: {e}")
        return {**state, "response": "I could not find that in the documents."}

async def chat_node(state: AgentState) -> AgentState:
    try:
        from app.services.world_model import record_interaction
        llm = get_llm()
        personal_context = state.get("personal_context", "")
        emotional_prefix = get_emotional_prefix(state["user_input"])

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                f"You are NAVIX, a friendly personal AI assistant.\n"
                f"{personal_context}\n"
                f"Keep responses under 3 sentences. Be warm and natural."
            )),
            HumanMessage(content=state["user_input"])
        ])
        messages = prompt.format_messages()
        result = await llm.ainvoke(messages)
        initial = emotional_prefix + result.content

        # self-reflection — improve answer
        from core.reflection import reflect_and_improve
        improved = await reflect_and_improve(state["user_input"], initial)

        # record to world model
        await record_interaction(state["user_input"], "chat")

        return {**state, "response": improved}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {**state, "response": "Sorry, something went wrong."}

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
            return {**state, "response": result}

        family_match = re.search(r"(\w+) is my (\w+)", text)
        if family_match:
            result = await add_family(family_match.group(1), family_match.group(2))
            return {**state, "response": result}

        fav_match = re.search(r"my favourite (\w+) is (.+)", text)
        if fav_match:
            result = await set_favourite(fav_match.group(1), fav_match.group(2))
            return {**state, "response": result}

        await add_memory(state["user_input"])
        return {**state, "response": "Got it Naveen, I will remember that."}
    except Exception as e:
        logger.error(f"Memory error: {e}")
        return {**state, "response": "Sorry, could not save that memory."}

async def browser_node(state: AgentState) -> AgentState:
    try:
        from app.services.command_parser import execute_browser_command
        result = await execute_browser_command(state["user_input"])
        return {**state, "response": result or "Done."}
    except Exception as e:
        return {**state, "response": f"Browser error: {e}"}

async def pc_node(state: AgentState) -> AgentState:
    try:
        from app.services.pc_command_parser import execute_pc_command
        result = await execute_pc_command(state["user_input"])
        return {**state, "response": result or "Done."}
    except Exception as e:
        return {**state, "response": f"PC error: {e}"}

def route_to_tool(state: AgentState) -> Literal["rag", "chat", "browser", "pc", "memory"]:
    return state["tool"]

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("chat", chat_node)
    graph.add_node("browser", browser_node)
    graph.add_node("pc", pc_node)
    graph.add_node("memory", memory_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_to_tool,
        {
            "rag":     "rag",
            "chat":    "chat",
            "browser": "browser",
            "pc":      "pc",
            "memory":  "memory"
        }
    )

    graph.add_edge("rag",     END)
    graph.add_edge("chat",    END)
    graph.add_edge("browser", END)
    graph.add_edge("pc",      END)
    graph.add_edge("memory",  END)

    return graph.compile()

_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph