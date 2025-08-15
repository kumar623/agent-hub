from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class MarketState(BaseModel):
    question: str
    answer: str = ""

async def market_research(s: MarketState) -> MarketState:
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3)
    prompt = f"You're a B2B agritech SDR. Given the question:\n{ s.question }\nPropose lead sources, segments, and a 5-step outreach plan."
    s.answer = (await llm.ainvoke(prompt)).content
    return s
