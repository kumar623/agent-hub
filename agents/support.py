from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class SupportState(BaseModel):
    message: str
    reply: str = ""

async def triage(s: SupportState) -> SupportState:
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)
    sys = "You are first-line B2B support. Be brief, helpful, and capture issue category and urgency."
    s.reply = (await llm.ainvoke(f"{sys}\n\nCustomer said: {s.message}")).content
    return s
