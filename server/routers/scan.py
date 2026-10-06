"""Compatibility route that explicitly blocks the unsupported V1 scan runtime."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from capabilities import CapabilityApplication, capability_state, result_state
from routers.capabilities import capability_json, get_capability_application


router = APIRouter(prefix="/api")


@router.post("/scan/run")
def run_scan(
    capabilities: CapabilityApplication = Depends(get_capability_application),
) -> JSONResponse:
    runtime = capabilities.get("investigation.runtime")
    capability = capability_state(
        "legacy.scan",
        "Legacy V1 scan",
        "unavailable",
        "The V1 market/LLM scan is not a V2 investigation capability.",
        "signal-v2-investigation-contract@1",
        evaluated_at=runtime["evaluated_at"],
        reason_codes=["legacy_v1_scan_disabled", *runtime["reason_codes"]],
        unmet_prerequisites=runtime["unmet_prerequisites"],
    )
    return JSONResponse(
        status_code=409,
        content={
            "capability": capability_json(capability),
            "result": capability_json(
                result_state(
                    "error",
                    "Request rejected because the action is unsupported in V2.",
                    evaluated_at=runtime["evaluated_at"],
                )
            ),
        },
    )
