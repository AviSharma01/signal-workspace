from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from db.database import get_connection
from watch_events import WatchApplication
from jobs.watch_events import schedule_watch_expiry
from routers.events import event_json


router = APIRouter(prefix="/api/watch-events", tags=["watch-events"])
_application = WatchApplication(get_connection)


class AdmissionCommand(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
    event_id: str = Field(min_length=1)


def get_watch_application() -> WatchApplication:
    return _application


@router.get("")
def list_watch_events(application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        return event_json(application.list(population="real"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/admissions", status_code=status.HTTP_201_CREATED)
def admit_watch_event(command: AdmissionCommand,
                      application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        result = application.admit(command.event_id, population="real")
        schedule_watch_expiry(application=application)
        return event_json(result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Event not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{watch_event_id}")
def read_watch_event(watch_event_id: str,
                     application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        return event_json(application.get(watch_event_id, population="real"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Watch Event not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{watch_event_id}/active-eligibility")
def authorize_active_action(watch_event_id: str,
                            application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        result = application.authorize_active_action(watch_event_id, population="real")
        schedule_watch_expiry(application=application)
        return event_json(result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Watch Event not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{watch_event_id}/assessments/{assessment_id}/reproduction")
def reproduce_assessment(watch_event_id: str, assessment_id: str,
                         application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        application.recorded_assessment(watch_event_id, assessment_id, population="real")
        return event_json(application.reproduce(assessment_id, population="real"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Watch Event assessment not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{watch_event_id}/assessments/{assessment_id}/recomputation")
def recompute_assessment(watch_event_id: str, assessment_id: str,
                         application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        application.recorded_assessment(watch_event_id, assessment_id, population="real")
        return event_json(application.historical_recompute(assessment_id, population="real"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Watch Event assessment not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{watch_event_id}/assessments/{assessment_id}/corrected-retrospective")
def corrected_retrospective_assessment(
    watch_event_id: str,
    assessment_id: str,
    as_of: int = Query(alias="asOf", ge=0),
    application: WatchApplication = Depends(get_watch_application),
) -> dict:
    try:
        application.recorded_assessment(watch_event_id, assessment_id, population="real")
        return event_json(application.corrected_retrospective(assessment_id, population="real", as_of=as_of))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Watch Event assessment not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{watch_event_id}/assessments/{assessment_id}")
def read_recorded_assessment(watch_event_id: str, assessment_id: str,
                             application: WatchApplication = Depends(get_watch_application)) -> dict:
    try:
        return event_json(application.recorded_assessment(watch_event_id, assessment_id, population="real"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Watch Event assessment not found") from exc
