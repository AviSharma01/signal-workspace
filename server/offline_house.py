"""The approved, fixed F2 test corpus. No discovery, uploads or source requests."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path

from disclosures import ArtifactIntegrityError, DisclosureApplication, RetrievedArtifact
from disclosure_sources import house_filing_url
from house_ptr import METHOD, VERSION


MANIFEST_VERSION = "f2-offline-house@1"
FIXTURE_ROOT = Path(__file__).parent / "tests/fixtures/house_ptr"


@dataclass(frozen=True)
class CorpusEntry:
    key: str
    sha256: str
    byte_length: int
    pages: int
    expected_row_starts: int | None
    characteristics: str

    @property
    def year(self) -> int:
        return int(self.key.split("-")[0])

    @property
    def document_id(self) -> str:
        return self.key.split("-")[1]

    @property
    def source_url(self) -> str:
        return house_filing_url(self.year, self.document_id)


CORPUS = (
    CorpusEntry("2021-20018021", "071aab65d8223132ac372501605fadc98948e3c8f0faa006931ea3902c86d7c2", 56079, 1, 1, "Native table; spouse owner and wrapped amount."),
    CorpusEntry("2026-20034556", "f019e347ac3f85903d590ff6d742f79cecfb4a9ece6eaa78e7a62e4d76167790", 68943, 2, 5, "Native table; source row IDs and Amended text; no amendment relationship established."),
    CorpusEntry("2025-20030699", "ac87f8583b66599886a5e6e8f7d8161f01f1d7b169013c906b17bec3f9a8ac00", 97617, 5, 33, "Native multipage table with repeated headers."),
    CorpusEntry("2018-9113416", "4d0dd27bee198e990a38754ac8eed00410dd7678bdc1968f4a2f27b6c99986da", 32908, 1, None, "Handwritten scan; no native text; transaction count unknown; OCR unsupported."),
    CorpusEntry("2018-20010021", "f3a1c8471c966a464081f9a2af94dac3e2a51a4234ffc590bdba4b1579f8ece2", 55475, 2, 5, "Native table; three equal Disney rows are distinct occurrences."),
    CorpusEntry("2025-20030387", "f96b24ba647c43bed680b256edc545059a62274d4785abe3ba36c94d653ce220", 366564, 41, 296, "Partial native table; unresolved continuations on pages 16/18; completeness unestablished."),
)


class CorpusError(ValueError):
    def __init__(self, status_code: int, reason: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.detail = {"reasonCode": reason, "message": message, "retryable": retryable}


def entry_for(key: str) -> CorpusEntry:
    for entry in CORPUS:
        if entry.key == key:
            return entry
    raise CorpusError(404, "offline_entry_not_found", "No such declared offline filing.")


def _local_path(entry: CorpusEntry) -> Path:
    path = FIXTURE_ROOT / f"{entry.key}.pdf"
    if FIXTURE_ROOT.resolve() != FIXTURE_ROOT or path.is_symlink():
        raise CorpusError(409, "offline_file_unsafe", "The declared fixture path must not contain symlinks.")
    return path


def _local_status(entry: CorpusEntry) -> str:
    try:
        info = _local_path(entry).lstat()
        return "present_unverified" if stat.S_ISREG(info.st_mode) and info.st_nlink == 1 else "unsafe"
    except FileNotFoundError:
        return "missing"
    except (OSError, CorpusError):
        return "unsafe"


def observe(entry: CorpusEntry, application: DisclosureApplication) -> dict:
    try:
        descriptor = os.open(_local_path(entry), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise CorpusError(409, "offline_file_unsafe", "The declared fixture must be a regular, unaliased file.")
            content = stream.read(entry.byte_length + 1)
    except OSError as exc:
        raise CorpusError(503, "offline_file_unavailable", "The declared retained sample is unavailable locally.", retryable=True) from exc
    application.verify_retained_content(content, entry.sha256, entry.byte_length)
    return application.ingest_house_filing(RetrievedArtifact(
        population="test", source_name="house-clerk", source_url=entry.source_url,
        media_type="application/pdf", content=content, retrieved_at_ms=int(time.time() * 1000),
        purpose="manual", freshness_status="unknown", coverage_status="unknown", http_status=None,
        source_metadata={"observationKind": "offline_sample_read", "originalRetrievedAt": None,
                         "liveSourceAvailability": "unknown", "manifest": "tests/fixtures/house_ptr/README.md",
                         "corpusVersion": MANIFEST_VERSION, "corpusEntry": entry.key},
    ), report_year=entry.year, document_id=entry.document_id)


def _entry_evidence(entry: CorpusEntry, evidence: dict) -> dict | None:
    for artifact in evidence["artifacts"]:
        if (artifact["sourceUrl"] != entry.source_url or artifact["sourceName"] != "house-clerk"
                or artifact["sourceAuthority"] != "official" or artifact["artifactKind"] != "original_filing"):
            continue
        versions = [v for v in artifact["versions"] if v["contentSha256"] == entry.sha256]
        ids = {v["id"] for v in versions}
        observations = [o for o in artifact["retrievalObservations"]
                        if o["artifactVersionId"] in ids
                        and o["sourceMetadata"].get("observationKind") == "offline_sample_read"
                        and o["availabilityStatus"] == "available" and o["httpStatus"] is None]
        if versions and observations:
            return {**artifact, "versions": versions, "retrievalObservations": observations}
    return None


def _verified_version(entry: CorpusEntry, artifact: dict, application: DisclosureApplication) -> dict:
    version = artifact["versions"][0]
    detail = application.get_artifact_version(artifact["id"], version["id"], population="test")
    application.verify_retained_content(detail["rawContent"], entry.sha256, entry.byte_length)
    application.verify_retained_content(detail["rawContent"], detail["contentSha256"], detail["contentLength"])
    return version


def resume(entry: CorpusEntry, application: DisclosureApplication) -> dict:
    artifact = _entry_evidence(entry, application.query_evidence(population="test"))
    if artifact is None:
        raise CorpusError(409, "offline_not_imported", "Import this declared sample before resuming processing.")
    version = _verified_version(entry, artifact, application)
    return application.resume_house_filing(version["id"], population="test",
                                          report_year=entry.year, document_id=entry.document_id)


def retained_content(artifact_id: str, version_id: str, application: DisclosureApplication) -> tuple[bytes, str]:
    evidence = application.query_evidence(population="test")
    for entry in CORPUS:
        artifact = _entry_evidence(entry, evidence)
        if artifact and artifact["id"] == artifact_id and artifact["versions"][0]["id"] == version_id:
            _verified_version(entry, artifact, application)
            detail = application.get_artifact_version(artifact_id, version_id, population="test")
            application.verify_retained_content(detail["rawContent"], entry.sha256, entry.byte_length)
            return detail["rawContent"], f"{entry.key}.pdf"
    raise CorpusError(404, "offline_version_not_found", "No such declared offline artifact version.")


def read_corpus(application: DisclosureApplication) -> dict:
    evidence = application.query_evidence(population="test")
    entries = []
    for entry in CORPUS:
        artifact = _entry_evidence(entry, evidence)
        filing = next((f for f in evidence["sourceFilings"] if artifact and f["id"] == artifact["sourceFilingRecordId"]), None)
        processing = "not_imported"
        integrity = "not_checked"
        extraction = None
        rows = []
        representation = {}
        if artifact:
            version = artifact["versions"][0]
            rows = version["rowOccurrences"]
            extraction = next((x for x in version["extractions"] if x["method"] == METHOD and x["methodVersion"] == VERSION), None)
            representation = (extraction["representation"] or {}) if extraction else {}
            processing = "extraction_pending"
            if not artifact["sourceFilingRecordId"]:
                processing = "filing_link_pending"
            elif extraction:
                expected = representation.get("rows", [])
                linked = filing and any(link["artifactVersionId"] == version["id"] and link["extractionId"] == extraction["id"]
                                        for link in filing["evidence"])
                if not linked:
                    processing = "filing_evidence_pending"
                elif len(rows) > len(expected) or any(r["ordinal"] >= len(expected) or r["rawFields"] != expected[r["ordinal"]] for r in rows):
                    processing = "reconciliation_error"
                elif len(rows) < len(expected):
                    processing = "rows_pending"
                elif any(not _has_normalization(row, extraction) for row in rows):
                    processing = "normalization_pending"
                else:
                    processing = "finished"
            try:
                _verified_version(entry, artifact, application)
                integrity = "verified"
            except ArtifactIntegrityError:
                integrity = "failed"
                processing = "integrity_error"

        normalized = sum(_has_normalization(row, extraction) for row in rows)
        fragments = representation.get("unresolvedFragments", [])
        matches = len(representation.get("rows", [])) == entry.expected_row_starts if extraction and entry.expected_row_starts is not None else None
        completeness = "unknown"
        if integrity == "verified" and extraction and extraction["status"] in {"succeeded", "partial"}:
            completeness = "matched_sample_expectation" if extraction["status"] == "succeeded" and matches else "partial"
        receipt = {"manifestVersion": MANIFEST_VERSION, "expectedSha256": entry.sha256,
                   "expectedRowStarts": entry.expected_row_starts, "extractedRowStarts": len(representation.get("rows", [])) if extraction else None,
                   "independentCountMatches": matches, "storedRows": len(rows), "normalizedRows": normalized,
                   "partialRows": sum(r["parseStatus"] == "partial" for r in rows),
                   "unresolvedFragmentCount": len(fragments), "completeness": completeness,
                   "engine": representation.get("engine"), "processingStatus": processing,
                   "extractionStatus": extraction["status"] if extraction else "not_attempted", "integrity": integrity}
        # Stable evidence fingerprint excludes generated IDs and actual instants.
        fingerprint = {"receipt": receipt, "rows": [{"ordinal": r["ordinal"], "rawFields": r["rawFields"],
                        "normalizations": [{k: n[k] for k in ("method", "methodVersion", "status", "normalizedFields", "issues")}
                                           for n in r["normalizations"]]} for r in rows], "fragments": fragments}
        receipt["reconciliationSha256"] = hashlib.sha256(json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if artifact:
            # Page text/word geometry stays in the retained extraction. The bounded
            # list response exposes page outcomes/fragments without megabytes of words.
            artifact = {**artifact, "versions": [{**v, "extractions": [{**x, "representation": {
                "engine": (x["representation"] or {}).get("engine"),
                "pages": [{"page": p["page"], "status": p["status"]} for p in (x["representation"] or {}).get("pages", [])],
                "issues": (x["representation"] or {}).get("issues", []),
                "unresolvedFragments": (x["representation"] or {}).get("unresolvedFragments", []),
            }} for x in v["extractions"]]} for v in artifact["versions"]]}
        entries.append({"key": entry.key, "reportYear": entry.year, "documentId": entry.document_id,
                        "sourceUrl": entry.source_url, "expectedSha256": entry.sha256, "expectedBytes": entry.byte_length,
                        "expectedPages": entry.pages, "characteristics": entry.characteristics,
                        "locatorProvenance": "official_annual_index" if entry.year in {2018, 2021} else "legacy_disclosure_locator",
                        "retentionScope": "isolated_offline_test_only", "localCopyStatus": _local_status(entry),
                        "imported": artifact is not None, "processingStatus": processing,
                        "extractionStatus": receipt["extractionStatus"], "receipt": receipt, "artifact": artifact,
                        "sourceFiling": filing})
    return {"mode": "offline_retained_corpus", "population": "test", "manifestVersion": MANIFEST_VERSION,
            "liveAcquisitionPermitted": False, "reasonCode": "house_live_access_unresolved",
            "detail": "Isolated retained test samples. Original retrieval/publication times, live availability, freshness and coverage remain unknown. No annual indexes are retained.",
            "entries": entries, "importedCount": sum(e["imported"] for e in entries)}


def _has_normalization(row: dict, extraction: dict | None) -> bool:
    return extraction is not None and any(
        n["method"] == "house-ptr-fields" and n["methodVersion"] == "1" and n["extractionId"] == extraction["id"]
        for n in row["normalizations"]
    )
