from fastapi import APIRouter, Depends, HTTPException, Query

from capabilities import CapabilityApplication, result_state
from db.database import get_connection
from investigation_contract import RunCommand
from investigations import InvestigationApplication
from routers.capabilities import capability_json, get_capability_application

router = APIRouter(prefix='/api/investigations', tags=['investigations'])


def get_investigation_application(
    capabilities: CapabilityApplication = Depends(get_capability_application),
) -> InvestigationApplication:
    return InvestigationApplication(get_connection, capabilities)


def investigation_json(value):
    # Retained source content is never camelized or rewritten.
    if isinstance(value, list):
        return [investigation_json(item) for item in value]
    if isinstance(value, dict):
        from pydantic.alias_generators import to_camel
        return {to_camel(key): item if key == 'content' else investigation_json(item)
                for key, item in value.items()}
    return value


def run_response(run, capabilities):
    capability = capabilities.get('investigation.runtime')
    state = {'ready': 'empty', 'completed': 'successful', 'incomplete': 'partial',
             'unavailable': 'partial', 'review_required': 'error'}[run['status']]
    return {'capability': capability_json(capability),
            'result': capability_json(result_state(state, f"Investigation run is {run['status']}.",
                                                  evaluated_at=capability['evaluated_at'])),
            'run': investigation_json(run)}


def _error(exc):
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail='Event, Watch Event or investigation run not found')
    return HTTPException(status_code=422, detail='Investigation command or retained output failed application validation')


@router.post('', status_code=201)
def create_run(command: RunCommand,
               application: InvestigationApplication = Depends(get_investigation_application),
               capabilities: CapabilityApplication = Depends(get_capability_application)):
    try:
        return run_response(application.create(command.model_dump(), population='real'), capabilities)
    except (ValueError, KeyError) as exc:
        raise _error(exc) from exc


@router.get('')
def list_runs(event_id: str | None = Query(default=None, alias='eventId'),
              ticker: str | None = None, limit: int = Query(default=50, ge=1),
              application: InvestigationApplication = Depends(get_investigation_application),
              capabilities: CapabilityApplication = Depends(get_capability_application)):
    try:
        runs = application.list(population='real', event_id=event_id, ticker=ticker, limit=limit)
        capability = capabilities.get('investigation.runtime')
        state = 'empty' if not runs else 'partial' if any(run['status'] != 'completed' for run in runs) else 'successful'
        return {'capability': capability_json(capability),
                'result': capability_json(result_state(state, 'Retained investigation runs loaded.', evaluated_at=capability['evaluated_at'])),
                'runs': investigation_json(runs)}
    except ValueError as exc:
        raise _error(exc) from exc


@router.get('/{run_id}')
def read_run(run_id: str, application: InvestigationApplication = Depends(get_investigation_application),
             capabilities: CapabilityApplication = Depends(get_capability_application)):
    try:
        return run_response(application.get(run_id, population='real'), capabilities)
    except (ValueError, KeyError) as exc:
        raise _error(exc) from exc


@router.post('/{run_id}/execute')
def execute_run(run_id: str, application: InvestigationApplication = Depends(get_investigation_application),
                capabilities: CapabilityApplication = Depends(get_capability_application)):
    try:
        return run_response(application.execute(run_id, population='real'), capabilities)
    except (ValueError, KeyError) as exc:
        raise _error(exc) from exc


@router.get('/{run_id}/reproduction')
def reproduce_run(run_id: str, application: InvestigationApplication = Depends(get_investigation_application)):
    try:
        return investigation_json(application.reproduce(run_id, population='real'))
    except (ValueError, KeyError) as exc:
        raise _error(exc) from exc
