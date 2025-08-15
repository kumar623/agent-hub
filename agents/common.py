import os, json, asyncio, httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

SUPABASE_URL = os.getenv("SUPABASE_URL","")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY","")
SUPABASE_DSN = os.getenv("SUPABASE_DSN","")
TENANT_ID = os.getenv("TENANT_ID","t-demo")

API_BASE = os.getenv("API_BASE","")
API_KEY = os.getenv("API_KEY","")
BACKEND_MODE = os.getenv("BACKEND_MODE","simple")
SOP_FILE = os.getenv("SOP_FILE","sop.defaults.json")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL","")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS","30"))
APPLY_CHANGES = os.getenv("APPLY_CHANGES","false").lower()=="true"

HEADERS = {"Content-Type":"application/json"}
if TENANT_ID: HEADERS["X-Tenant-Id"]=TENANT_ID
if API_KEY:   HEADERS["x-api-key"]=API_KEY

def load_sop() -> Dict[str, Any]:
    with open(SOP_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

async def http_get(path: str) -> Dict[str,Any]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as cx:
        r = await cx.get(f"{API_BASE}{path}", headers=HEADERS)
        r.raise_for_status(); return r.json()

async def http_post(path: str, payload: Dict[str,Any]) -> Dict[str,Any]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as cx:
        r = await cx.post(f"{API_BASE}{path}", headers=HEADERS, json=payload)
        r.raise_for_status(); return r.json()

async def slack(text: str):
    if not SLACK_WEBHOOK_URL: return
    async with httpx.AsyncClient(timeout=15) as cx:
        try: await cx.post(SLACK_WEBHOOK_URL, json={"text": text})
        except: pass

async def get_fleet() -> List[Dict[str,Any]]:
    if BACKEND_MODE=="v1":
        data = await http_get("/api/v1/fleet")
        return data.get("items",[])
    # simple: fallback to default or GET /devices if exists
    try:
        data = await http_get("/devices")
        devs = data.get("devices", data) or []
        return [{"id": d.get("id") or d.get("device_id") or d.get("name")} for d in devs]
    except Exception:
        return [{"id": os.getenv("DEFAULT_CONTAINER_ID","container-001")}]

async def latest(container_id: str) -> Dict[str,Any]:
    if BACKEND_MODE=="v1":
        data = await http_get(f"/api/v1/telemetry/latest?scope=container&id={container_id}")
        return data.get("latest",{})
    data = await http_get(f"/telemetry/latest?device_id={container_id}")
    return data.get("latest", data)

async def post_setpoints(container_id: str, targets: Dict[str,Any], justification: str) -> Dict[str,Any]:
    if BACKEND_MODE=="v1":
        body={"scope":"container","id":container_id,"targets":targets,"justification":justification,"approval_required":True}
        return await http_post("/api/v1/setpoints", body)
    body={"device_id":container_id}
    mapping={"temp_c":"target_temp_c","humidity":"target_humidity","co2_ppm":"target_co2_ppm","ph":"target_ph","ec_ms_cm":"target_ec_ms_cm","light_ppfd":"target_light_ppfd"}
    for k,v in targets.items():
        if k in mapping: body[mapping[k]]=v
    return await http_post("/control/setpoints", body)
