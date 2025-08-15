from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class FinanceState(BaseModel):
    question: str
    answer: str = ""

async def finance_snapshot(s: FinanceState) -> FinanceState:
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)
    prompt = f"Act as a fractional CFO. For this ask:\n{s.question}\nReturn a cashflow snapshot outline, KPI list, and unit-economics checks."
    s.answer = (await llm.ainvoke(prompt)).content
    return s
