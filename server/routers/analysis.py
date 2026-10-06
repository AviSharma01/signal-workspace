from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import Field
from pydantic.alias_generators import to_camel

from analysis import AnalysisApplication
from cohort_analysis import CohortAnalysisApplication
from db.database import get_connection
from event_contract import Command
from routers.events import event_json


router = APIRouter(prefix='/api/analysis', tags=['analysis'])
_application = AnalysisApplication(get_connection)
_cohorts = CohortAnalysisApplication(get_connection)


def get_analysis_application() -> AnalysisApplication:
    return _application


def get_cohort_application() -> CohortAnalysisApplication:
    return _cohorts


def cohort_json(value):
    """Preserve dynamic reason/identity/count keys while normalizing record fields."""
    if isinstance(value, list):
        return [cohort_json(item) for item in value]
    if isinstance(value, dict):
        maps = {'reason_counts', 'counts', 'chambers'}
        return {to_camel(key): event_json(item) if key == 'source_input' else
                item if key in maps else cohort_json(item) for key, item in value.items()}
    return value


class CohortCommand(Command):
    source_run_id: str = Field(min_length=1)


@router.get('/cohorts')
def read_cohorts(population: None = Query(default=None),
                 application: CohortAnalysisApplication = Depends(get_cohort_application)):
    return cohort_json(application.query(population='real'))


@router.post('/cohorts')
def execute_cohort(command: CohortCommand,
                   application: CohortAnalysisApplication = Depends(get_cohort_application)):
    try:
        response = application.execute(population='real', **command.model_dump())
        return JSONResponse(status_code=409 if response['capability']['availability'] != 'available' else 201,
                            content=cohort_json(response))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Retained outcome run not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get('/cohorts/{run_id}')
def read_cohort_run(run_id: str, population: None = Query(default=None),
                    application: CohortAnalysisApplication = Depends(get_cohort_application)):
    try:
        run = application.get_run(run_id, population='real')
        return cohort_json({'capability': application.query(population='real')['capability'],
                           'result': run['result'], 'runs': [run]})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Cohort run not found') from exc


@router.get('/cohorts/{run_id}/reproduction')
def reproduce_cohort_run(run_id: str, population: None = Query(default=None),
                         application: CohortAnalysisApplication = Depends(get_cohort_application)):
    try:
        return cohort_json(application.reproduce(run_id, population='real'))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Cohort run not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class AnalysisCommand(Command):
    event_view_id: str = Field(min_length=1)
    market_input_id: str = Field(min_length=1)


@router.get('')
def read_analysis(population: None = Query(default=None),
                  application: AnalysisApplication = Depends(get_analysis_application)) -> dict:
    return event_json(application.query(population='real'))


@router.post('/runs')
def execute_analysis(command: AnalysisCommand,
                     application: AnalysisApplication = Depends(get_analysis_application)):
    try:
        response = application.execute(population='real', **command.model_dump())
        return JSONResponse(status_code=409 if response['capability']['availability'] != 'available' else 201,
                            content=event_json(response))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Retained Analysis input not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get('/runs/{run_id}')
def read_run(run_id: str, population: None = Query(default=None),
             application: AnalysisApplication = Depends(get_analysis_application)) -> dict:
    try:
        run = application.get_run(run_id, population='real')
        return event_json({'capability': application.query(population='real')['capability'],
                           'result': run['result'], 'runs': [run]})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Analysis run not found') from exc


@router.get('/runs/{run_id}/reproduction')
def reproduce_run(run_id: str, population: None = Query(default=None),
                  application: AnalysisApplication = Depends(get_analysis_application)) -> dict:
    try:
        return event_json(application.reproduce(run_id, population='real'))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Analysis run not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
