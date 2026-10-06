from fastapi import APIRouter, Depends, HTTPException, Query

from capabilities import CapabilityApplication, result_state
from investigations import InvestigationApplication
from routers.capabilities import capability_json, get_capability_application
from routers.investigations import get_investigation_application, investigation_json

router = APIRouter(prefix='/api')


@router.get('/findings')
def get_findings(
    ticker: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
    capabilities: CapabilityApplication = Depends(get_capability_application),
    application: InvestigationApplication = Depends(get_investigation_application),
) -> dict:
    capability = capabilities.get('investigation.runtime')
    try:
        runs = application.list(population='real', ticker=ticker, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='Retained Findings failed application validation') from exc
    findings = [run['finding'] for run in runs if run['finding'] is not None]
    state = 'empty' if not findings else 'partial' if any(run['status'] != 'completed' for run in runs) else 'successful'
    return {
        'capability': capability_json(capability),
        'result': capability_json(result_state(state, 'Only application-validated V2 Findings are exposed.',
                                              evaluated_at=capability['evaluated_at'])),
        'findings': investigation_json(findings),
        'legacyDataExcluded': True,
    }
