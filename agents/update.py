from datetime import datetime, timezone
from typing import Dict, Any
from .common import get_fleet, latest

async def daily_text() -> str:
    fleet = await get_fleet()
    lines = ["*Daily Ops Summary*"]
    keys = ["ph","ec_ms_cm","temp_c","humidity","co2_ppm","light_ppfd"]
    for item in fleet:
        cid = item["id"]; lt = await latest(cid)
        badges = [f"{k}:{lt.get(k)}" for k in keys if lt.get(k) is not None]
        lines.append(f"• {cid}: " + ", ".join(badges))
    return "\n".join(lines)
