from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic.alias_generators import to_camel

from db.database import get_connection
from event_contract import EvidenceAssertion, ViewCommand
from events import EventApplication


router = APIRouter(prefix="/api/events", tags=["events"])
_application = EventApplication(get_connection)


def get_event_application() -> EventApplication:
    return _application


def event_json(value, *, preserve_keys=False):
    """Normalize record keys at the API boundary, preserving source/dynamic maps."""
    if isinstance(value, list):
        return [event_json(item, preserve_keys=preserve_keys) for item in value]
    if isinstance(value, dict):
        if preserve_keys:
            return value
        preserved_maps = {"rawFields", "normalizedFields", "representation", "fields", "reasonCounts",
                          "chambers", "directions", "calendarYears", "sourceRoles"}
        return {to_camel(key): event_json(item, preserve_keys=key in preserved_maps) for key, item in value.items()}
    return value


@router.get("")
def read_events(
    perspective: Literal["public_information", "system_observation"],
    as_of: int = Query(alias="asOf", ge=0),
    population: None = Query(default=None),
    application: EventApplication = Depends(get_event_application),
) -> dict:
    try:
        return event_json(application.derive(population="real", perspective=perspective, as_of=as_of))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/evidence-assertions", status_code=status.HTTP_201_CREATED)
def record_assertion(
    command: EvidenceAssertion,
    application: EventApplication = Depends(get_event_application),
) -> dict:
    try:
        return event_json(application.record_assertion(command.model_dump(mode="json", exclude_unset=True), population="real"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/views", status_code=status.HTTP_201_CREATED)
def record_view(
    command: ViewCommand,
    application: EventApplication = Depends(get_event_application),
) -> dict:
    try:
        return event_json(application.record_view(population="real", **command.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/views/{view_id}")
def read_recorded_view(
    view_id: str,
    population: None = Query(default=None),
    application: EventApplication = Depends(get_event_application),
) -> dict:
    try:
        return event_json(application.get_recorded_view(view_id, population="real"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Event view not found") from exc


@router.get("/views/{view_id}/reproduction")
def reproduce_recorded_view(
    view_id: str,
    population: None = Query(default=None),
    application: EventApplication = Depends(get_event_application),
) -> dict:
    try:
        return event_json(application.reproduce_recorded_view(view_id, population="real"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Event view not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
