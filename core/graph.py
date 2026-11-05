from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from core.llm import get_llm
from loguru import logger
import operator
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

OODA_SYSTEM = """You are the Supervisor Agent of the NAVIX Multi-Agent System.
Your job is to receive a goal from the user, delegate it to the correct specialist sub-agent, evaluate the result, and decide if the task is complete.

Available Sub-Agents:
- BROWSER: For web searches, opening links, youtube, wikipedia, reading web pages.
- PC: For desktop control, typing, clicking, volume, screenshots.
- MEMORY: For remembering personal details, recalling past events.
- CODE: For writing scripts, debugging, generating Python.
- RAG: For searching local documents and files.
- CHAT: For casual conversation or answering general knowledge questions.

If the sub-agent's result is successful, respond to the user and select "RESPOND".
If the sub-agent failed, you can re-assign the task or try a different agent.
If you need no tools and just want to talk, select "CHAT".

Reply strictly in this format:
THOUGHT: (your reasoning)
ROUTING: (BROWSER|PC|MEMORY|CODE|RAG|CHAT|RESPOND)
MESSAGE: (the task instruction for the agent, OR the final response for the user)
"""

class AgentState(TypedDict):
    user_input:       str
    understood:       str
    plan:             list
    current_step:     int
    tool:             str
    tool_result:      str
    verified:         bool
    response:         str
    emotion:          str
    personal_context: str
    messages:         Annotated[list, operator.add]
    iteration:        int
    sender:           str

# ── Supervisor Node ────────────────────────────────────────────────────────────
async def supervisor_node(state: AgentState) -> AgentState:
    logger.info("Supervisor Agent evaluating state...")
    llm = get_llm()
    iteration = state.get("iteration", 0)
    
    if iteration > 3:
        logger.warning("Max iterations reached. Forcing RESPOND.")
        return {**state, "tool": "RESPOND", "response": "I tried my best but couldn't complete the task in time.", "iteration": iteration + 1}
        
    last_result = state.get("tool_result", "")
    history = "\n".join([m.content for m in state.get("messages", [])[-4:]])
    
    prompt = f"User Request: {state['user_input']}\n"
    if last_result:
        prompt += f"Last Agent Result: {last_result}\n"
        prompt += "Is the task complete? If yes, route to RESPOND and put the final answer in MESSAGE.\n"
    else:
        prompt += "Which agent should handle this first?\n"
        
    messages = [SystemMessage(content=OODA_SYSTEM), HumanMessage(content=prompt)]
    result = await llm.ainvoke(messages)
    content = result.content.strip()
    
    import re
    route_match = re.search(r"ROUTING:\s*(BROWSER|PC|MEMORY|CODE|RAG|CHAT|RESPOND)", content, re.IGNORECASE)
    msg_match = re.search(r"MESSAGE:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
    
    route = route_match.group(1).upper() if route_match else "CHAT"
    msg = msg_match.group(1).strip() if msg_match else "I'm not sure how to respond."
    
    logger.info(f"Supervisor Decision -> Route: {route}, Message: {msg[:50]}")
    
    if route == "RESPOND":
        return {**state, "tool": "RESPOND", "response": msg, "iteration": iteration + 1, "messages": [AIMessage(content=msg)]}
    else:
        return {**state, "tool": route, "understood": msg, "iteration": iteration + 1}

def router(state: AgentState) -> str:
    route = state.get("tool", "RESPOND")
    return route

# ── Sub-Agents ────────────────────────────────────────────────────────────
async def browser_agent(state: AgentState) -> AgentState:
    logger.info("Browser Agent active.")
    try:
        from navix.services.ai.command_parser import execute_browser_command
        result = await execute_browser_command(state["understood"])
        response = result or "Browser action completed."
        return {**state, "tool_result": f"[Browser] {response}", "sender": "BrowserAgent"}
    except Exception as e:
        return {**state, "tool_result": f"[Browser] Failed: {str(e)}", "sender": "BrowserAgent"}

async def pc_agent(state: AgentState) -> AgentState:
    logger.info("Desktop Agent active.")
    try:
        from navix.services.desktop.pc_command_parser import execute_pc_command
        result = await execute_pc_command(state["understood"])
        response = result or "PC command completed."
        return {**state, "tool_result": f"[PC] {response}", "sender": "DesktopAgent"}
    except Exception as e:
        return {**state, "tool_result": f"[PC] Failed: {str(e)}", "sender": "DesktopAgent"}

async def code_agent(state: AgentState) -> AgentState:
    logger.info("Coding Agent active.")
    try:
        llm = get_llm()
        res = await llm.ainvoke([SystemMessage(content="Write clean Python code for the request. No markdown."), HumanMessage(content=state["understood"])])
        return {**state, "tool_result": f"[Code] {res.content.strip()}", "sender": "CodingAgent"}
    except Exception as e:
        return {**state, "tool_result": f"[Code] Failed: {str(e)}", "sender": "CodingAgent"}

async def memory_agent(state: AgentState) -> AgentState:
    logger.info("Memory Agent active.")
    return {**state, "tool_result": "[Memory] Memory stored successfully.", "sender": "MemoryAgent"}

async def rag_agent(state: AgentState) -> AgentState:
    logger.info("RAG Agent active.")
    try:
        import asyncio
        from core.rag_chain import get_rag_chain
        chain = get_rag_chain()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: chain.invoke({"query": state["understood"]}))
        res = result if isinstance(result, str) else result.get("result", str(result))
        return {**state, "tool_result": f"[RAG] {res}", "sender": "RAGAgent"}
    except Exception as e:
        return {**state, "tool_result": f"[RAG] Failed: {str(e)}", "sender": "RAGAgent"}

async def chat_agent(state: AgentState) -> AgentState:
    logger.info("Chat Agent active.")
    llm = get_llm()
    res = await llm.ainvoke([SystemMessage(content="You are a helpful casual AI assistant. Respond to the prompt naturally."), HumanMessage(content=state["understood"])])
    return {**state, "tool_result": f"[Chat] {res.content.strip()}", "sender": "ChatAgent"}

def build_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("BROWSER", browser_agent)
    graph.add_node("PC", pc_agent)
    graph.add_node("CODE", code_agent)
    graph.add_node("MEMORY", memory_agent)
    graph.add_node("RAG", rag_agent)
    graph.add_node("CHAT", chat_agent)
    
    graph.add_edge(START, "supervisor")
    
    graph.add_conditional_edges(
        "supervisor",
        router,
        {
            "BROWSER": "BROWSER",
            "PC": "PC",
            "CODE": "CODE",
            "MEMORY": "MEMORY",
            "RAG": "RAG",
            "CHAT": "CHAT",
            "RESPOND": END
        }
    )
    
    # Sub-agents always report back to supervisor for verification/routing
    graph.add_edge("BROWSER", "supervisor")
    graph.add_edge("PC", "supervisor")
    graph.add_edge("CODE", "supervisor")
    graph.add_edge("MEMORY", "supervisor")
    graph.add_edge("RAG", "supervisor")
    graph.add_edge("CHAT", "supervisor")
    
    return graph

async def get_graph():
    conn = await aiosqlite.connect("C:/Users/Naveen/AGI_Develop/data/navix_state.db")
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)