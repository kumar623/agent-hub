from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class MeetingState(BaseModel):
    transcript: str
    summary: str = ""

async def summarize(s: MeetingState) -> MeetingState:
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)
    sys = "You are an ops lead. Output sections: Summary, Decisions, Action Items (owner, due). Be concise."
    s.summary = (await llm.ainvoke(f"{sys}\n\nTranscript:\n{s.transcript}")).content
    return s
