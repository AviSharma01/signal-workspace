from fastapi import APIRouter, Depends, Query

from capabilities import CapabilityApplication, result_state
from routers.capabilities import capability_json, get_capability_application

router = APIRouter(prefix="/api")


@router.get("/findings")
def get_findings(
    ticker: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
    capabilities: CapabilityApplication = Depends(get_capability_application),
) -> dict:
    del ticker, limit
    capability = capabilities.get("investigation.runtime")
    return {
        "capability": capability_json(capability),
        "result": capability_json(
            result_state(
                "empty",
                "Legacy V1 findings are excluded from the V2 investigation surface.",
                evaluated_at=capability["evaluated_at"],
            )
        ),
        "findings": [],
        "legacyDataExcluded": True,
    }
