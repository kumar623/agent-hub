import os, asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.ops import build_ops_graph, OpsState
from agents.meeting import MeetingState, summarize
from agents.update import daily_text
from agents.market import MarketState, market_research
from agents.support import SupportState, triage
from agents.finance import FinanceState, finance_snapshot

load_dotenv()
app = FastAPI(title="DANS Agent Hub (LangGraph)")

# ===== Schemas
class OpsReq(BaseModel):
    container_id: str

class ChatReq(BaseModel):
    question: str
    container_id: str | None = None

class MeetingReq(BaseModel):
    transcript: str

class GenericQ(BaseModel):
    question: str

# ===== Health
@app.get("/health")
async def health():
    return {"ok": True}

# ===== Ops Agent
ops_graph = build_ops_graph()

@app.post("/ops/run")
async def ops_run(req: OpsReq):
    state = OpsState(container_id=req.container_id)
    out = await ops_graph.ainvoke(state)
    return {
        "container_id": req.container_id,
        "breaches": out["breaches"],
        "proposed": out["proposed"],
        "suggestion": out["suggestion"]
    }

# ===== Meeting Agent
@app.post("/meeting/summarize")
async def meeting_summarize(req: MeetingReq):
    st = MeetingState(transcript=req.transcript)
    res = await summarize(st)
    return {"summary": res.summary}

# ===== Update Agent (daily text)
@app.post("/update/daily")
async def update_daily():
    text = await daily_text()
    return {"text": text}

# ===== Market Agent
@app.post("/market/research")
async def market_q(req: GenericQ):
    st = MarketState(question=req.question)
    res = await market_research(st)
    return {"answer": res.answer}

# ===== Support Agent
@app.post("/support/triage")
async def support_triage(req: GenericQ):
    st = SupportState(message=req.question)
    res = await triage(st)
    return {"reply": res.reply}

# ===== Finance Agent
@app.post("/finance/snapshot")
async def finance_q(req: GenericQ):
    st = FinanceState(question=req.question)
    res = await finance_snapshot(st)
    return {"answer": res.answer}
