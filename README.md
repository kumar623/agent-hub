# DANS Agent Hub (LangGraph)

This is a single FastAPI service that hosts 6 agents built with LangGraph + OpenAI:

- Ops Agent `/ops/run`
- Meeting Agent `/meeting/summarize`
- Update Agent `/update/daily`
- Market Agent `/market/research`
- Support Agent `/support/triage`
- Finance Agent `/finance/snapshot`

## Setup

1) Copy `.env.example` → `.env` and fill values (OpenAI, Supabase, API_BASE).
2) Install & run:
   ```bash
   pip install -r requirements.txt
   uvicorn app:app --reload
