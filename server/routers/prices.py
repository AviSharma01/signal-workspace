from contextlib import AbstractContextManager
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from capabilities import CapabilityApplication, result_state
from db.database import get_connection
from routers.capabilities import capability_json, get_capability_application

router = APIRouter(prefix="/api")

@router.get("/prices/{company_id}")
def get_prices(
    company_id: str,
    range: str = Query(default="1D", pattern="^(1D|1W|1M|3M)$"),
    connection: AbstractContextManager[Any] = Depends(get_connection),
    capabilities: CapabilityApplication = Depends(get_capability_application),
) -> dict:
    cid = company_id.upper()
    del range

    with connection as conn:
        if not conn.execute("SELECT id FROM companies WHERE id = ?", (cid,)).fetchone():
            raise HTTPException(status_code=404, detail="Company not found")
    capability = capabilities.get("market.outcomes")
    return {
        "capability": capability_json(capability),
        "result": capability_json(
            result_state(
                "empty",
                "No production price result was requested because market outcomes are unavailable.",
                evaluated_at=capability["evaluated_at"],
            )
        ),
        "prices": [],
        "legacyDataExcluded": True,
    }
