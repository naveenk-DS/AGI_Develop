import json
import os
from pathlib import Path
from loguru import logger
from core.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

GRAPH_FILE = Path("F:/naveen/AGI_Start/data/knowledge_graph.json")

# in-memory graph
_graph = {
    "nodes": {},   # id -> {label, type, description}
    "edges": []    # [{from, to, relation}]
}

def load_graph():
    global _graph
    try:
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
        if GRAPH_FILE.exists():
            _graph = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
            logger.info(f"Graph loaded: {len(_graph['nodes'])} nodes, {len(_graph['edges'])} edges")
    except Exception as e:
        logger.error(f"Graph load error: {e}")

def save_graph():
    try:
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_FILE.write_text(
            json.dumps(_graph, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"Graph save error: {e}")

def add_node(node_id: str, label: str, node_type: str, description: str = ""):
    _graph["nodes"][node_id] = {
        "label": label,
        "type": node_type,
        "description": description
    }

def add_edge(from_id: str, to_id: str, relation: str):
    edge = {"from": from_id, "to": to_id, "relation": relation}
    if edge not in _graph["edges"]:
        _graph["edges"].append(edge)

def get_connected(node_id: str, depth: int = 2) -> list:
    visited = set()
    result = []

    def traverse(nid, d):
        if d == 0 or nid in visited:
            return
        visited.add(nid)
        node = _graph["nodes"].get(nid)
        if node:
            result.append({
                "id": nid,
                "label": node["label"],
                "type": node["type"],
                "description": node["description"]
            })
        for edge in _graph["edges"]:
            if edge["from"] == nid:
                result.append({"relation": edge["relation"]})
                traverse(edge["to"], d - 1)
            elif edge["to"] == nid:
                result.append({"relation": f"reverse: {edge['relation']}"})
                traverse(edge["from"], d - 1)

    traverse(node_id, depth)
    return result

async def extract_entities_and_relations(text: str) -> dict:
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=(
                "Extract entities and relationships from text. "
                "Return ONLY valid JSON in this exact format:\n"
                '{"entities": [{"id": "e1", "label": "Python", "type": "technology", "description": "programming language"}], '
                '"relations": [{"from": "e1", "to": "e2", "relation": "used_for"}]}'
            )),
            HumanMessage(content=f"Extract entities and relations from:\n\n{text[:1000]}")
        ]
        result = await llm.ainvoke(messages)
        raw = result.content.strip()

        # clean JSON
        import re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data
        return {"entities": [], "relations": []}
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        return {"entities": [], "relations": []}

async def add_document_to_graph(text: str, doc_name: str):
    data = await extract_entities_and_relations(text)

    entities = data.get("entities", [])
    relations = data.get("relations", [])

    # add doc node
    doc_id = f"doc_{doc_name.replace(' ', '_')}"
    add_node(doc_id, doc_name, "document", f"Document: {doc_name}")

    for entity in entities:
        eid = entity.get("id", "")
        if eid:
            add_node(
                eid,
                entity.get("label", ""),
                entity.get("type", "concept"),
                entity.get("description", "")
            )
            add_edge(doc_id, eid, "contains")

    for rel in relations:
        if rel.get("from") and rel.get("to"):
            add_edge(rel["from"], rel["to"], rel.get("relation", "related_to"))

    save_graph()
    logger.info(f"Graph updated: +{len(entities)} entities, +{len(relations)} relations from {doc_name}")
    return len(entities), len(relations)

async def graph_search(query: str) -> str:
    try:
        # find relevant nodes by label match
        query_lower = query.lower()
        relevant_nodes = []

        for node_id, node in _graph["nodes"].items():
            if (query_lower in node["label"].lower() or
                query_lower in node.get("description", "").lower()):
                relevant_nodes.append(node_id)

        if not relevant_nodes:
            return ""

        # get connected context
        context_parts = []
        for node_id in relevant_nodes[:3]:
            connected = get_connected(node_id, depth=2)
            node = _graph["nodes"].get(node_id, {})
            context_parts.append(
                f"{node.get('label', node_id)} ({node.get('type', 'concept')}): "
                f"{node.get('description', '')}"
            )
            for item in connected:
                if "relation" in item:
                    context_parts.append(f"  -> {item['relation']}")
                elif "label" in item:
                    context_parts.append(f"  -> {item['label']}: {item.get('description', '')}")

        return "\n".join(context_parts[:20])
    except Exception as e:
        logger.error(f"Graph search error: {e}")
        return ""

def get_graph_stats() -> dict:
    return {
        "nodes": len(_graph["nodes"]),
        "edges": len(_graph["edges"]),
        "node_types": list(set(n["type"] for n in _graph["nodes"].values())),
        "top_nodes": sorted(
            _graph["nodes"].items(),
            key=lambda x: sum(1 for e in _graph["edges"]
                            if e["from"] == x[0] or e["to"] == x[0]),
            reverse=True
        )[:5]
    }

# load on import
load_graph()