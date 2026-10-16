from __future__ import annotations

import base64
import binascii
import hashlib
import re
import sqlite3
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from capabilities import CapabilityApplication, result_state
from db.database import get_connection
from disclosure_sources import HouseDisclosureSource, house_filing_url, house_index_url
from disclosures import ArtifactIntegrityError, DisclosureApplication, RetrievedArtifact
import offline_house
from routers.capabilities import capability_json, get_capability_application


router = APIRouter(prefix="/api/disclosures", tags=["disclosures"])
OFFLINE_SAMPLE = Path(__file__).parents[1] / "tests/fixtures/house_ptr/2021-20018021.pdf"
OFFLINE_SAMPLE_SHA256 = "071aab65d8223132ac372501605fadc98948e3c8f0faa006931ea3902c86d7c2"
OFFLINE_SAMPLE_URL = house_filing_url(2021, "20018021")


class OfflineSampleCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


def get_disclosure_application() -> DisclosureApplication:
    return _application


def get_house_source() -> HouseDisclosureSource:
    raise HTTPException(status_code=409, detail={
        "reasonCode": "house_live_access_unresolved",
        "message": "Live House acquisition and retained-copy permissions remain unresolved. Use the isolated offline sample.",
    })


def _validate_house_locator(report_year: int, document_id: str | None = None) -> None:
    try:
        if document_id is None:
            house_index_url(report_year)
        else:
            house_filing_url(report_year, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _offline_evidence(application: DisclosureApplication) -> dict:
    evidence = application.query_evidence(population="test")
    artifacts = []
    for artifact in evidence["artifacts"]:
        if artifact["sourceUrl"] != OFFLINE_SAMPLE_URL or artifact["sourceAuthority"] != "official":
            continue
        versions = [version for version in artifact["versions"] if version["contentSha256"] == OFFLINE_SAMPLE_SHA256]
        version_ids = {version["id"] for version in versions}
        observations = [item for item in artifact["retrievalObservations"]
                        if item["artifactVersionId"] in version_ids
                        and item["sourceMetadata"].get("observationKind") == "offline_sample_read"]
        if versions and observations:
            artifacts.append({**artifact, "versions": versions, "retrievalObservations": observations})
    filing_ids = {row["sourceFiling"]["id"] for artifact in artifacts for version in artifact["versions"]
                  for row in version["rowOccurrences"] if row["sourceFiling"]}
    return {"population": "test", "artifacts": artifacts,
            "sourceFilings": [filing for filing in evidence["sourceFilings"] if filing["id"] in filing_ids]}


def _offline_result(operation):
    try:
        return operation()
    except offline_house.CorpusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except ArtifactIntegrityError as exc:
        raise HTTPException(status_code=409, detail={"reasonCode": "offline_integrity_failed",
                            "message": "Retained sample integrity failed. Processing was blocked.", "retryable": False}) from exc
    except sqlite3.DatabaseError as exc:
        retryable = isinstance(exc, sqlite3.OperationalError) and any(word in str(exc).lower() for word in ("locked", "busy"))
        raise HTTPException(status_code=503, detail={"reasonCode": "offline_database_busy" if retryable else "offline_database_error",
                            "message": "Offline storage is busy; reload status and retry." if retryable else "Offline storage could not be processed. Preserve the database for inspection.",
                            "retryable": retryable}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"reasonCode": "offline_processing_conflict",
                            "message": "Retained processing records conflict. Preserve the database for inspection.", "retryable": False}) from exc


@router.get("/offline-corpus")
def read_offline_corpus(application: DisclosureApplication = Depends(get_disclosure_application)) -> dict:
    return _offline_result(lambda: offline_house.read_corpus(application))


@router.post("/offline-corpus/{entry_key}/observations", status_code=status.HTTP_201_CREATED)
def inspect_offline_entry(entry_key: str, command: OfflineSampleCommand,
                          application: DisclosureApplication = Depends(get_disclosure_application)) -> dict:
    return _offline_result(lambda: offline_house.observe(offline_house.entry_for(entry_key), application))


@router.post("/offline-corpus/{entry_key}/resume")
def resume_offline_entry(entry_key: str, command: OfflineSampleCommand,
                         application: DisclosureApplication = Depends(get_disclosure_application)) -> dict:
    return _offline_result(lambda: offline_house.resume(offline_house.entry_for(entry_key), application))


@router.get("/offline-corpus/artifacts/{artifact_id}/versions/{version_id}/content")
def download_offline_entry(artifact_id: str, version_id: str,
                           application: DisclosureApplication = Depends(get_disclosure_application)) -> Response:
    content, filename = _offline_result(lambda: offline_house.retained_content(artifact_id, version_id, application))
    return Response(content=content, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store",
    })


@router.get("/offline-sample")
def read_offline_sample(application: DisclosureApplication = Depends(get_disclosure_application)) -> dict:
    return {
        "mode": "offline_retained_sample", "population": "test",
        "filing": {"reportYear": 2021, "documentId": "20018021", "sourceUrl": OFFLINE_SAMPLE_URL},
        "expectedSha256": OFFLINE_SAMPLE_SHA256,
        "liveAcquisitionPermitted": False, "reasonCode": "house_live_access_unresolved",
        "detail": "Offline retained official sample only. Local reads prove no live source availability, freshness or publication time.",
        "evidence": _offline_evidence(application),
    }


@router.post("/offline-sample/observations", status_code=status.HTTP_201_CREATED)
def inspect_offline_sample(command: OfflineSampleCommand,
                          application: DisclosureApplication = Depends(get_disclosure_application)) -> dict:
    try:
        content = OFFLINE_SAMPLE.read_bytes()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="The declared retained sample is unavailable locally.") from exc
    if hashlib.sha256(content).hexdigest() != OFFLINE_SAMPLE_SHA256:
        raise HTTPException(status_code=409, detail="Retained sample integrity failed; no observation was recorded.")
    result = application.ingest_house_filing(RetrievedArtifact(
        population="test", source_name="house-clerk", source_url=OFFLINE_SAMPLE_URL,
        media_type="application/pdf", content=content, retrieved_at_ms=int(time.time() * 1000),
        purpose="manual", freshness_status="unknown", coverage_status="unknown", http_status=None,
        source_metadata={"observationKind": "offline_sample_read", "originalRetrievedAt": None,
                         "liveSourceAvailability": "unknown", "manifest": "tests/fixtures/house_ptr/README.md"},
    ), report_year=2021, document_id="20018021")
    return {**result, "mode": "offline_retained_sample", "population": "test"}


@router.get("/offline-sample/artifacts/{artifact_id}/versions/{version_id}/content")
def download_offline_sample(artifact_id: str, version_id: str,
                            application: DisclosureApplication = Depends(get_disclosure_application)) -> Response:
    evidence = _offline_evidence(application)
    if not any(artifact["id"] == artifact_id and any(version["id"] == version_id for version in artifact["versions"])
               for artifact in evidence["artifacts"]):
        raise HTTPException(status_code=404, detail="Offline sample version not found")
    detail = application.get_artifact_version(artifact_id, version_id, population="test")
    if hashlib.sha256(detail["rawContent"]).hexdigest() != OFFLINE_SAMPLE_SHA256:
        raise HTTPException(status_code=409, detail="Retained sample integrity failed.")
    return Response(content=detail["rawContent"], media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="2021-20018021.pdf"',
        "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store",
    })


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
    capabilities: CapabilityApplication = Depends(get_capability_application),
) -> dict:
    if population is not None:
        raise HTTPException(status_code=422, detail="the public API exposes only the real population")
    evidence = application.query_evidence(population="real")
    capability = capabilities.get("disclosure.evidence_retention")
    state, detail = application.assess_evidence_result(evidence)
    return {
        **evidence,
        "capability": capability_json(capability),
        "result": capability_json(
            result_state(state, detail, evaluated_at=capability["evaluated_at"])
        ),
    }


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
    readiness = application.query_chamber_readiness(population="real")
    evaluated_at = max(item["evaluated_at"] for item in readiness.values())
    return capability_json({
        **readiness,
        "result": result_state(
            "successful",
            "Chamber readiness gates were evaluated independently of source result records.",
            evaluated_at=evaluated_at,
        ),
    })
