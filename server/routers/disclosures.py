from __future__ import annotations

import base64
import binascii
import re
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from db.database import get_connection
from disclosure_sources import HouseDisclosureSource, house_filing_url, house_index_url
from disclosures import DisclosureApplication, RetrievedArtifact


router = APIRouter(prefix="/api/disclosures", tags=["disclosures"])


class RetrievalCommand(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    purpose: Literal["daily_discovery", "startup_catch_up", "reconciliation", "manual"]


class SupportingRetrievalCommand(RetrievalCommand):
    source_name: str = Field(alias="sourceName", min_length=1, max_length=80)
    source_url: str = Field(alias="sourceUrl", min_length=1, max_length=2048)
    media_type: str = Field(alias="mediaType", min_length=1, max_length=120)
    payload_base64: str = Field(alias="payloadBase64")
    freshness_status: Literal["current", "stale", "unknown"] = Field(alias="freshnessStatus")
    coverage_status: Literal["complete", "partial", "unknown"] = Field(alias="coverageStatus")

    @field_validator("source_name")
    @classmethod
    def supporting_source_only(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", value):
            raise ValueError("sourceName must be a lowercase source key")
        if value in {"house-clerk", "senate-efd"}:
            raise ValueError("official sources must use their authoritative retrieval route")
        return value


class ReprocessCommand(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    extraction_method_version: Literal["1", "2"] = Field(alias="extractionMethodVersion")
    normalization_method_version: Literal["1", "2"] = Field(alias="normalizationMethodVersion")


_application = DisclosureApplication(get_connection)
_house_source = HouseDisclosureSource()


def get_disclosure_application() -> DisclosureApplication:
    return _application


def get_house_source() -> HouseDisclosureSource:
    return _house_source


def _validate_house_locator(report_year: int, document_id: str | None = None) -> None:
    try:
        if document_id is None:
            house_index_url(report_year)
        else:
            house_filing_url(report_year, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/supporting-retrievals", status_code=status.HTTP_201_CREATED)
def ingest_supporting_retrieval(
    command: SupportingRetrievalCommand,
    application: DisclosureApplication = Depends(get_disclosure_application),
) -> dict:
    try:
        content = base64.b64decode(command.payload_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail="payloadBase64 is invalid") from exc
    return application.ingest_supporting_retrieval(
        RetrievedArtifact(
            population="real",
            source_name=command.source_name,
            source_url=command.source_url,
            media_type=command.media_type,
            content=content,
            retrieved_at_ms=int(time.time() * 1000),
            purpose=command.purpose,
            freshness_status=command.freshness_status,
            coverage_status=command.coverage_status,
        )
    )


@router.post(
    "/house/indexes/{report_year}/retrievals",
    status_code=status.HTTP_201_CREATED,
)
def retrieve_house_index(
    report_year: int,
    command: RetrievalCommand,
    application: DisclosureApplication = Depends(get_disclosure_application),
    source: HouseDisclosureSource = Depends(get_house_source),
) -> dict:
    _validate_house_locator(report_year)
    fetched = source.fetch_index(report_year)
    return application.ingest_house_index(
        RetrievedArtifact.from_house_source(fetched, purpose=command.purpose),
        report_year=report_year,
    )


@router.post(
    "/house/filings/{report_year}/{document_id}/retrievals",
    status_code=status.HTTP_201_CREATED,
)
def retrieve_house_filing(
    report_year: int,
    document_id: str,
    command: RetrievalCommand,
    application: DisclosureApplication = Depends(get_disclosure_application),
    source: HouseDisclosureSource = Depends(get_house_source),
) -> dict:
    _validate_house_locator(report_year, document_id)
    fetched = source.fetch_filing(report_year, document_id)
    return application.ingest_house_filing(
        RetrievedArtifact.from_house_source(fetched, purpose=command.purpose),
        report_year=report_year,
        document_id=document_id,
    )


@router.get("/evidence")
def get_evidence(
    population: str | None = Query(default=None),
    application: DisclosureApplication = Depends(get_disclosure_application),
) -> dict:
    if population is not None:
        raise HTTPException(status_code=422, detail="the public API exposes only the real population")
    return application.query_evidence(population="real")


@router.get("/artifacts/{artifact_id}/versions/{version_id}")
def get_artifact_version(
    artifact_id: str,
    version_id: str,
    application: DisclosureApplication = Depends(get_disclosure_application),
) -> dict:
    try:
        detail = application.get_artifact_version(
            artifact_id,
            version_id,
            population="real",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="artifact version not found") from exc
    raw_content = detail.pop("rawContent")
    detail["rawContentBase64"] = base64.b64encode(raw_content).decode()
    return detail


@router.post("/artifacts/{artifact_id}/versions/{version_id}/extractions")
def reprocess_artifact_version(
    artifact_id: str,
    version_id: str,
    command: ReprocessCommand,
    application: DisclosureApplication = Depends(get_disclosure_application),
) -> dict:
    try:
        application.get_artifact_version(artifact_id, version_id, population="real")
        return application.reprocess_artifact_version(
            version_id,
            population="real",
            extracted_at_ms=int(time.time() * 1000),
            extraction_method_version=command.extraction_method_version,
            normalization_method_version=command.normalization_method_version,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="artifact version not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/readiness")
def get_readiness(
    application: DisclosureApplication = Depends(get_disclosure_application),
) -> dict:
    return application.query_chamber_readiness(population="real")
