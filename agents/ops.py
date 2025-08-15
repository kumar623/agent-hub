import json
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from .common import load_sop, latest, post_setpoints, slack, APPLY_CHANGES

class OpsState(BaseModel):
    container_id: str
    latest: Dict[str, Any] = Field(default_factory=dict)
    sop: Dict[str, Any] = Field(default_factory=load_sop)
    breaches: List[Dict[str,Any]] = Field(default_factory=list)
    proposed: Dict[str, Any] = Field(default_factory=dict)
    suggestion: str = ""

def _severity(metric: str, value: Optional[float], sop: Dict[str,Any]) -> str:
    if value is None: return "low"
    low, high = sop[metric]["min"], sop[metric]["max"]
    margin = (high-low)*0.05
    if value < low - margin or value > high + margin: return "high"
    if value < low or value > high: return "medium"
    return "low"

def _propose(metric: str, value: Optional[float], sop: Dict[str,Any]) -> Optional[float]:
    if value is None: return None
    target = sop[metric]["target"]; max_delta = sop[metric]["max_delta"]
    diff = target - value
    if abs(diff) < 1e-6: return None
    if value < sop[metric]["min"] or value > sop[metric]["max"] or abs(diff) >= (0.5*max_delta):
        step = max(-max_delta, min(max_delta, diff))
        new_val = value + step
        return round(target if abs(diff) > max_delta else round(new_val,3), 3)
    return None

async def fetch_node(state: OpsState) -> OpsState:
    state.latest = await latest(state.container_id)
    return state

async def analyze_node(state: OpsState) -> OpsState:
    sop = state.sop; lt = state.latest
    breaches=[]; proposed={}
    for k in ["ph","ec_ms_cm","temp_c","humidity","co2_ppm","light_ppfd"]:
        v = lt.get(k)
        sev = _severity(k, v, sop)
        if sev in ("medium","high"):
            breaches.append({"metric":k,"value":float(v),"severity":sev,"range":f"{sop[k]['min']}-{sop[k]['max']}","target":sop[k]["target"]})
            nv = _propose(k, float(v), sop)
            if nv is not None: proposed[k]=nv
    state.breaches = breaches; state.proposed = proposed
    return state

async def suggest_node(state: OpsState) -> OpsState:
    if not state.breaches:
        state.suggestion = "All good — no breaches detected."
        return state
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)
    prompt = f"""You are a careful CEA operations manager.
SOPs: {json.dumps(state.sop)}
Latest: {json.dumps(state.latest)}
Breaches: {json.dumps(state.breaches)}
Proposed targets: {json.dumps(state.proposed)}
Write <=6 short bullets with checks, risks, and gentle corrections."""
    state.suggestion = (await llm.ainvoke(prompt)).content
    return state

async def apply_node(state: OpsState) -> OpsState:
    if not state.proposed: return state
    just = " | ".join([f"{b['metric']}:{b['value']} vs {b['range']} (→ {b['target']})" for b in state.breaches])
    await slack(f"🔎 Ops: {state.container_id} breaches: " + ", ".join([f"{b['metric']}={b['value']}" for b in state.breaches]))
    if APPLY_CHANGES:
        await post_setpoints(state.container_id, state.proposed, just)
    return state

# Build the graph
def build_ops_graph():
    g = StateGraph(OpsState)
    g.add_node("fetch", fetch_node)
    g.add_node("analyze", analyze_node)
    g.add_node("suggest", suggest_node)
    g.add_node("apply", apply_node)
    g.set_entry_point("fetch")
    g.add_edge("fetch","analyze")
    g.add_edge("analyze","suggest")
    g.add_edge("suggest","apply")
    g.add_edge("apply", END)
    return g.compile()
