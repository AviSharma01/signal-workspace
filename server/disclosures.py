from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from io import BytesIO
from typing import Any, Callable, ContextManager

from disclosure_sources import (
    SAFE_RETRIEVAL_METADATA_KEYS,
    FetchedSourceArtifact,
    house_filing_url,
    house_index_url,
)
from house_ptr import METHOD as PTR_METHOD, VERSION as PTR_VERSION, extract_ptr, normalize_ptr_row


ConnectionFactory = Callable[[], ContextManager[sqlite3.Connection]]


@dataclass(frozen=True)
class RetrievedArtifact:
    population: str
    source_name: str
    source_url: str
    media_type: str
    content: bytes | None
    retrieved_at_ms: int
    purpose: str
    freshness_status: str
    coverage_status: str
    source_metadata: dict[str, Any] = field(default_factory=dict)
    http_status: int | None = 200
    availability_status: str = "available"

    @classmethod
    def from_house_source(
        cls,
        fetched: FetchedSourceArtifact,
        *,
        purpose: str,
    ) -> RetrievedArtifact:
        return cls(
            population="real",
            source_name="house-clerk",
            source_url=fetched.source_url,
            media_type=fetched.media_type,
            content=fetched.content,
            retrieved_at_ms=fetched.retrieved_at_ms,
            purpose=purpose,
            freshness_status="unknown",
            coverage_status="unknown",
            source_metadata={
                key: value
                for key, value in fetched.source_metadata.items()
                if key.lower() in {item.lower() for item in SAFE_RETRIEVAL_METADATA_KEYS}
            },
            http_status=fetched.http_status,
            availability_status=fetched.availability_status,
        )


class DisclosureApplication:
    def __init__(self, connection_factory: ConnectionFactory):
        self._connection_factory = connection_factory

    def ingest_supporting_retrieval(self, retrieval: RetrievedArtifact) -> dict[str, Any]:
        if retrieval.content is None or retrieval.availability_status != "available":
            raise ValueError("supporting payload ingestion requires retrieved content")
        recorded = self._record_retrieval(
            retrieval,
            source_authority="supporting",
            artifact_kind="supporting_payload",
        )
        if recorded["versionCreated"]:
            parse_result = self._extract_supporting_json(
                version_id=recorded["artifactVersionId"],
                retrieval=retrieval,
            )
            recorded.update(parse_result)
        else:
            recorded.update(
                parseStatus=self._version_parse_status(recorded["artifactVersionId"]),
                sourceFilingsDiscovered=0,
                rowOccurrencesCreated=0,
            )
        return recorded

    def ingest_house_index(
        self,
        retrieval: RetrievedArtifact,
        *,
        report_year: int,
    ) -> dict[str, Any]:
        expected_url = house_index_url(report_year)
        self._validate_official_house_retrieval(retrieval, expected_url)
        recorded = self._record_retrieval(
            retrieval,
            source_authority="official",
            artifact_kind="house_annual_index",
        )
        if retrieval.availability_status != "available":
            recorded.update(
                parseStatus="not_attempted",
                sourceFilingsDiscovered=0,
                rowOccurrencesCreated=0,
            )
        elif recorded["versionCreated"]:
            recorded.update(
                self._extract_house_index(
                    recorded["artifactVersionId"],
                    retrieval,
                )
            )
        else:
            recorded.update(
                parseStatus=self._version_parse_status(recorded["artifactVersionId"]),
                sourceFilingsDiscovered=0,
                rowOccurrencesCreated=0,
            )
        recorded["filingDocumentIds"] = (
            self._house_filing_ids_for_version(recorded["artifactVersionId"])
            if recorded["artifactVersionId"] is not None
            else []
        )
        return recorded

    def ingest_house_filing(
        self,
        retrieval: RetrievedArtifact,
        *,
        report_year: int,
        document_id: str,
    ) -> dict[str, Any]:
        expected_url = house_filing_url(report_year, document_id)
        self._validate_official_house_retrieval(retrieval, expected_url)
        recorded = self._record_retrieval(
            retrieval,
            source_authority="official",
            artifact_kind="original_filing",
        )
        if retrieval.availability_status == "available":
            with self._connection_factory() as conn:
                filing_record_id, _ = self._ensure_source_filing_with_connection(
                    conn,
                    population=retrieval.population,
                    source_name="house-clerk",
                    source_filing_id=document_id,
                    chamber="house",
                    source_url=retrieval.source_url,
                    discovered_at_ms=retrieval.retrieved_at_ms,
                    raw_metadata={"DocID": document_id, "Year": str(report_year)},
                )
                conn.execute(
                    """
                    UPDATE disclosure_artifacts SET source_filing_record_id = ? WHERE id = ?
                    """,
                    (filing_record_id, recorded["artifactId"]),
                )
            recorded.update(self._process_house_ptr(
                recorded["artifactVersionId"], population=retrieval.population,
                extracted_at_ms=int(time.time() * 1000),
            ))
            return recorded
        parse_status = (
            self._version_parse_status(recorded["artifactVersionId"])
            if recorded["artifactVersionId"] is not None
            else "not_attempted"
        )
        recorded.update(
            parseStatus=parse_status,
            sourceFilingsDiscovered=0,
            rowOccurrencesCreated=0,
        )
        return recorded

    def _process_house_ptr(
        self, version_id: str, *, population: str, extracted_at_ms: int,
    ) -> dict[str, Any]:
        with self._connection_factory() as conn:
            version = conn.execute(
                """SELECT v.raw_content, a.source_filing_record_id
                   FROM disclosure_artifact_versions v
                   JOIN disclosure_artifacts a ON a.id = v.artifact_id
                   WHERE v.id = ? AND a.population = ? AND a.source_name = 'house-clerk'
                     AND a.source_authority = 'official' AND a.artifact_kind = 'original_filing'""",
                (version_id, population),
            ).fetchone()
            if version is None:
                raise KeyError(version_id)
            successful_observation = conn.execute(
                """SELECT id FROM disclosure_retrieval_observations
                   WHERE artifact_version_id = ? AND availability_status = 'available'
                   LIMIT 1""", (version_id,),
            ).fetchone()
            if version["source_filing_record_id"] is None or successful_observation is None:
                raise ValueError("House PTR extraction requires a linked filing and successful retrieval observation")
            extraction = conn.execute(
                """SELECT id, status, representation_json FROM disclosure_extractions
                   WHERE artifact_version_id = ? AND method = ? AND method_version = ?""",
                (version_id, PTR_METHOD, PTR_VERSION),
            ).fetchone()
        if extraction is None:
            result = extract_ptr(bytes(version["raw_content"]))
            extraction_id = str(uuid.uuid4())
            representation = result["representation"]
            parse_status = result["status"]
            # Commit the entire extracted representation before row materialization
            # or normalization. A retry can resume from this durable representation.
            with self._connection_factory() as conn:
                conn.execute(
                    """INSERT INTO disclosure_extractions
                       (id, artifact_version_id, method, method_version, extracted_at,
                        status, representation_json, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (extraction_id, version_id, PTR_METHOD, PTR_VERSION, extracted_at_ms,
                     parse_status, json.dumps(representation, separators=(",", ":")),
                     "; ".join(representation["issues"]) or None),
                )
        else:
            extraction_id = extraction["id"]
            representation = json.loads(extraction["representation_json"])
            parse_status = extraction["status"]
        created = 0
        with self._connection_factory() as conn:
            self._link_source_filing_evidence(
                conn, filing_record_id=version["source_filing_record_id"],
                artifact_version_id=version_id, extraction_id=extraction_id,
                source_record_key="filing", observed_at_ms=extracted_at_ms,
            )
            for ordinal, row in enumerate(representation["rows"]):
                stored = conn.execute(
                    "SELECT id, raw_fields_json FROM disclosure_row_occurrences WHERE artifact_version_id = ? AND ordinal = ?",
                    (version_id, ordinal),
                ).fetchone()
                if stored is not None:
                    if json.loads(stored["raw_fields_json"]) != row:
                        raise ValueError("PTR extraction changed a source occurrence; correspondence is unresolved")
                    continue
                row_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO disclosure_row_occurrences
                       (id, artifact_version_id, source_filing_record_id, ordinal, raw_fields_json, parse_status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (row_id, version_id, version["source_filing_record_id"], ordinal,
                     json.dumps(row, separators=(",", ":")), row["parseStatus"]),
                )
                created += 1
        # Literal extracted rows are also durable before normalization is attempted.
        with self._connection_factory() as conn:
            rows = conn.execute(
                "SELECT id, raw_fields_json FROM disclosure_row_occurrences WHERE artifact_version_id = ? ORDER BY ordinal",
                (version_id,),
            ).fetchall()
            for stored in rows:
                prior = conn.execute(
                    "SELECT id FROM disclosure_normalizations WHERE row_occurrence_id = ? AND method = 'house-ptr-fields' AND method_version = '1'",
                    (stored["id"],),
                ).fetchone()
                if prior is not None:
                    continue
                row = json.loads(stored["raw_fields_json"])
                normalized, issues = normalize_ptr_row(row)
                issues = sorted(set(issues + row["issues"]))
                conn.execute(
                    """INSERT INTO disclosure_normalizations
                       (id, row_occurrence_id, extraction_id, method, method_version, normalized_at,
                        status, normalized_fields_json, issues_json)
                       VALUES (?, ?, ?, 'house-ptr-fields', '1', ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), stored["id"], extraction_id, int(time.time() * 1000),
                     "partial" if issues else "succeeded", json.dumps(normalized), json.dumps(issues)),
                )
        return {"extractionId": extraction_id, "parseStatus": parse_status,
                "sourceFilingsDiscovered": 0, "rowOccurrencesCreated": created}

    @staticmethod
    def _validate_official_house_retrieval(
        retrieval: RetrievedArtifact,
        expected_url: str,
    ) -> None:
        if retrieval.source_name != "house-clerk" or retrieval.source_url != expected_url:
            raise ValueError("official House evidence must come from its constructed Clerk URL")

    def _record_retrieval(
        self,
        retrieval: RetrievedArtifact,
        *,
        source_authority: str,
        artifact_kind: str,
        source_filing_db_id: str | None = None,
    ) -> dict[str, Any]:
        if retrieval.availability_status == "available" and retrieval.content is None:
            raise ValueError("an available retrieval must include content")
        content_hash = (
            hashlib.sha256(retrieval.content).hexdigest()
            if retrieval.content is not None
            else None
        )
        with self._connection_factory() as conn:
            artifact = conn.execute(
                """
                SELECT id FROM disclosure_artifacts
                WHERE population = ? AND source_name = ? AND artifact_kind = ? AND source_url = ?
                """,
                (
                    retrieval.population,
                    retrieval.source_name,
                    artifact_kind,
                    retrieval.source_url,
                ),
            ).fetchone()
            if artifact is None:
                artifact_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO disclosure_artifacts
                        (id, population, source_name, source_authority, artifact_kind,
                         source_filing_record_id, source_url, media_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        artifact_id,
                        retrieval.population,
                        retrieval.source_name,
                        source_authority,
                        artifact_kind,
                        source_filing_db_id,
                        retrieval.source_url,
                        retrieval.media_type,
                        retrieval.retrieved_at_ms,
                    ),
                )
            else:
                artifact_id = artifact["id"]
                if source_filing_db_id is not None:
                    conn.execute(
                        """
                        UPDATE disclosure_artifacts
                        SET source_filing_record_id = COALESCE(source_filing_record_id, ?)
                        WHERE id = ?
                        """,
                        (source_filing_db_id, artifact_id),
                    )

            if retrieval.content is None:
                version_created = False
                version_id = None
            else:
                version = conn.execute(
                    """
                    SELECT id FROM disclosure_artifact_versions
                    WHERE artifact_id = ? AND content_sha256 = ?
                    """,
                    (artifact_id, content_hash),
                ).fetchone()
                version_created = version is None
                if version_created:
                    version_id = str(uuid.uuid4())
                    conn.execute(
                        """
                        INSERT INTO disclosure_artifact_versions
                            (id, artifact_id, content_sha256, raw_content, content_length,
                             media_type, first_observed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            version_id,
                            artifact_id,
                            content_hash,
                            retrieval.content,
                            len(retrieval.content),
                            retrieval.media_type,
                            retrieval.retrieved_at_ms,
                        ),
                    )
                else:
                    version_id = version["id"]

            observation_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO disclosure_retrieval_observations
                    (id, artifact_id, artifact_version_id, observed_at, purpose,
                     availability_status, freshness_status, coverage_status,
                     http_status, source_metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    artifact_id,
                    version_id,
                    retrieval.retrieved_at_ms,
                    retrieval.purpose,
                    retrieval.availability_status,
                    retrieval.freshness_status,
                    retrieval.coverage_status,
                    retrieval.http_status,
                    json.dumps(retrieval.source_metadata, separators=(",", ":"), sort_keys=True),
                ),
            )

        return {
            "observationId": observation_id,
            "artifactId": artifact_id,
            "artifactVersionId": version_id,
            "versionCreated": version_created,
        }

    def _extract_house_index(
        self,
        version_id: str,
        retrieval: RetrievedArtifact,
    ) -> dict[str, Any]:
        extraction_id = str(uuid.uuid4())
        try:
            with zipfile.ZipFile(BytesIO(retrieval.content)) as archive:
                xml_names = [name for name in archive.namelist() if name.lower().endswith(".xml")]
                if len(xml_names) != 1:
                    raise ValueError("House index archive must contain exactly one XML member")
                root = ET.fromstring(archive.read(xml_names[0]))
            records = []
            for element in root:
                record = {child.tag: child.text or "" for child in element}
                if "DocID" not in record:
                    raise ValueError("House index record is missing DocID")
                records.append(record)
        except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError) as exc:
            with self._connection_factory() as conn:
                conn.execute(
                    """
                    INSERT INTO disclosure_extractions
                        (id, artifact_version_id, method, method_version, extracted_at,
                         status, representation_json, error)
                    VALUES (?, ?, 'house-index-xml', '1', ?, 'failed', NULL, ?)
                    """,
                    (extraction_id, version_id, retrieval.retrieved_at_ms, str(exc)),
                )
            return {
                "parseStatus": "failed",
                "sourceFilingsDiscovered": 0,
                "rowOccurrencesCreated": 0,
            }

        discovered_records = []
        with self._connection_factory() as conn:
            conn.execute(
                """
                INSERT INTO disclosure_extractions
                    (id, artifact_version_id, method, method_version, extracted_at,
                     status, representation_json, error)
                VALUES (?, ?, 'house-index-xml', '1', ?, 'succeeded', ?, NULL)
                """,
                (
                    extraction_id,
                    version_id,
                    retrieval.retrieved_at_ms,
                    json.dumps(records, separators=(",", ":"), sort_keys=True),
                ),
            )
            for ordinal, record in enumerate(records):
                filing_record_id, created = self._ensure_source_filing_with_connection(
                    conn,
                    population=retrieval.population,
                    source_name="house-clerk",
                    source_filing_id=record["DocID"],
                    chamber="house",
                    source_url=None,
                    discovered_at_ms=retrieval.retrieved_at_ms,
                    raw_metadata=record,
                )
                self._link_source_filing_evidence(
                    conn,
                    filing_record_id=filing_record_id,
                    artifact_version_id=version_id,
                    extraction_id=extraction_id,
                    source_record_key=str(ordinal),
                    observed_at_ms=retrieval.retrieved_at_ms,
                )
                if created:
                    discovered_records.append(record)
        return {
            "parseStatus": "succeeded",
            "sourceFilingsDiscovered": len(discovered_records),
            "discoveredFilings": discovered_records,
            "rowOccurrencesCreated": 0,
        }

    def _house_filing_ids_for_version(self, version_id: str) -> list[str]:
        with self._connection_factory() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT f.source_filing_id, f.raw_metadata_json
                FROM disclosure_source_filing_evidence AS e
                JOIN disclosure_source_filings AS f ON f.id = e.source_filing_record_id
                WHERE e.artifact_version_id = ?
                  AND f.source_name = 'house-clerk'
                ORDER BY f.source_filing_id
                """,
                (version_id,),
            ).fetchall()
        return [
            row["source_filing_id"]
            for row in rows
            if row["source_filing_id"].isdigit()
            and json.loads(row["raw_metadata_json"]).get("FilingType") == "P"
        ]

    def _ensure_source_filing(
        self,
        *,
        population: str,
        source_name: str,
        source_filing_id: str,
        chamber: str,
        source_url: str | None,
        discovered_at_ms: int,
        raw_metadata: dict[str, Any],
    ) -> tuple[str, bool]:
        with self._connection_factory() as conn:
            return self._ensure_source_filing_with_connection(
                conn,
                population=population,
                source_name=source_name,
                source_filing_id=source_filing_id,
                chamber=chamber,
                source_url=source_url,
                discovered_at_ms=discovered_at_ms,
                raw_metadata=raw_metadata,
            )

    @staticmethod
    def _ensure_source_filing_with_connection(
        conn: sqlite3.Connection,
        *,
        population: str,
        source_name: str,
        source_filing_id: str,
        chamber: str,
        source_url: str | None,
        discovered_at_ms: int,
        raw_metadata: dict[str, Any],
    ) -> tuple[str, bool]:
        existing = conn.execute(
            """
            SELECT id FROM disclosure_source_filings
            WHERE population = ? AND source_name = ? AND source_filing_id = ?
            """,
            (population, source_name, source_filing_id),
        ).fetchone()
        if existing is not None:
            if source_url is not None:
                conn.execute(
                    """
                    UPDATE disclosure_source_filings
                    SET source_url = COALESCE(source_url, ?)
                    WHERE id = ?
                    """,
                    (source_url, existing["id"]),
                )
            return existing["id"], False
        filing_record_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO disclosure_source_filings
                (id, population, source_name, source_filing_id, chamber,
                 source_url, discovered_at, raw_metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filing_record_id,
                population,
                source_name,
                source_filing_id,
                chamber,
                source_url,
                discovered_at_ms,
                json.dumps(raw_metadata, separators=(",", ":"), sort_keys=True),
            ),
        )
        return filing_record_id, True

    @staticmethod
    def _link_source_filing_evidence(
        conn: sqlite3.Connection,
        *,
        filing_record_id: str,
        artifact_version_id: str,
        extraction_id: str,
        source_record_key: str,
        observed_at_ms: int,
    ) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO disclosure_source_filing_evidence
                (id, source_filing_record_id, artifact_version_id, extraction_id,
                 source_record_key, observed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                filing_record_id,
                artifact_version_id,
                extraction_id,
                source_record_key,
                observed_at_ms,
            ),
        )

    def _extract_supporting_json(
        self,
        *,
        version_id: str,
        retrieval: RetrievedArtifact,
    ) -> dict[str, Any]:
        extraction_id = str(uuid.uuid4())
        try:
            parsed = json.loads(retrieval.content)
            rows = self._supporting_rows(parsed)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            with self._connection_factory() as conn:
                conn.execute(
                    """
                    INSERT INTO disclosure_extractions
                        (id, artifact_version_id, method, method_version, extracted_at,
                         status, representation_json, error)
                    VALUES (?, ?, 'supporting-json', '1', ?, 'failed', NULL, ?)
                    """,
                    (extraction_id, version_id, retrieval.retrieved_at_ms, str(exc)),
                )
            return {
                "parseStatus": "failed",
                "sourceFilingsDiscovered": 0,
                "rowOccurrencesCreated": 0,
            }

        filing_count = 0
        extraction_status = "partial" if any(not isinstance(row, dict) for row in rows) else "succeeded"
        with self._connection_factory() as conn:
            conn.execute(
                """
                INSERT INTO disclosure_extractions
                    (id, artifact_version_id, method, method_version, extracted_at,
                     status, representation_json, error)
                VALUES (?, ?, 'supporting-json', '1', ?, ?, ?, NULL)
                """,
                (
                    extraction_id,
                    version_id,
                    retrieval.retrieved_at_ms,
                    extraction_status,
                    json.dumps(rows, separators=(",", ":"), sort_keys=True),
                ),
            )
            for ordinal, row in enumerate(rows):
                filing_record_id = None
                source_filing_id = row.get("filing_id") if isinstance(row, dict) else None
                if isinstance(source_filing_id, str) and source_filing_id:
                    filing_record_id, created = self._ensure_source_filing_with_connection(
                        conn,
                        population=retrieval.population,
                        source_name=retrieval.source_name,
                        source_filing_id=source_filing_id,
                        chamber="unknown",
                        source_url=row.get("doc_url"),
                        discovered_at_ms=retrieval.retrieved_at_ms,
                        raw_metadata={"filing_id": source_filing_id},
                    )
                    filing_count += int(created)
                    self._link_source_filing_evidence(
                        conn,
                        filing_record_id=filing_record_id,
                        artifact_version_id=version_id,
                        extraction_id=extraction_id,
                        source_record_key=str(ordinal),
                        observed_at_ms=retrieval.retrieved_at_ms,
                    )

                row_occurrence_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO disclosure_row_occurrences
                        (id, artifact_version_id, source_filing_record_id, ordinal,
                         raw_fields_json, parse_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row_occurrence_id,
                        version_id,
                        filing_record_id,
                        ordinal,
                        json.dumps(row, separators=(",", ":"), sort_keys=True),
                        "parsed" if isinstance(row, dict) else "malformed",
                    ),
                )
                if isinstance(row, dict):
                    self._insert_normalization(
                        conn,
                        row_occurrence_id=row_occurrence_id,
                        extraction_id=extraction_id,
                        row=row,
                        method_version="1",
                        normalized_at_ms=retrieval.retrieved_at_ms,
                    )

        return {
            "parseStatus": extraction_status,
            "sourceFilingsDiscovered": filing_count,
            "rowOccurrencesCreated": len(rows),
        }

    @staticmethod
    def _supporting_rows(parsed: Any) -> list[Any]:
        if isinstance(parsed, list):
            rows = parsed
        elif isinstance(parsed, dict) and isinstance(parsed.get("trades"), list):
            rows = parsed["trades"]
        elif isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
            rows = parsed["data"]
        else:
            raise ValueError("supporting payload must be a list or contain a trades/data list")
        return rows

    def reprocess_artifact_version(
        self,
        version_id: str,
        *,
        population: str,
        extracted_at_ms: int,
        extraction_method_version: str,
        normalization_method_version: str,
    ) -> dict[str, Any]:
        with self._connection_factory() as conn:
            artifact = conn.execute(
                """SELECT a.artifact_kind FROM disclosure_artifacts a
                   JOIN disclosure_artifact_versions v ON v.artifact_id = a.id
                   WHERE v.id = ? AND a.population = ?""", (version_id, population),
            ).fetchone()
        if artifact is not None and artifact["artifact_kind"] == "original_filing":
            if extraction_method_version != PTR_VERSION or normalization_method_version != "1":
                raise ValueError("supported House PTR extraction/normalization versions are 1/1")
            return self._process_house_ptr(version_id, population=population, extracted_at_ms=extracted_at_ms)
        if extraction_method_version != "2" or normalization_method_version != "2":
            raise ValueError("the supported recomputation method versions are extraction=2 and normalization=2")
        with self._connection_factory() as conn:
            version = conn.execute(
                """
                SELECT v.raw_content
                FROM disclosure_artifact_versions AS v
                JOIN disclosure_artifacts AS a ON a.id = v.artifact_id
                WHERE v.id = ? AND a.population = ?
                  AND a.artifact_kind = 'supporting_payload'
                """,
                (version_id, population),
            ).fetchone()
            if version is None:
                raise KeyError(version_id)
            prior = conn.execute(
                """
                SELECT id, status FROM disclosure_extractions
                WHERE artifact_version_id = ? AND method = 'supporting-json'
                  AND method_version = ?
                """,
                (version_id, extraction_method_version),
            ).fetchone()
            if prior is not None:
                return {
                    "extractionId": prior["id"],
                    "parseStatus": prior["status"],
                    "rowOccurrencesCreated": 0,
                }

            parsed = json.loads(bytes(version["raw_content"]))
            rows = self._supporting_rows(parsed)
            if isinstance(parsed, list):
                container = "list"
            elif "trades" in parsed:
                container = "trades"
            else:
                container = "data"
            representation = {"container": container, "rows": rows}
            occurrences = conn.execute(
                """
                SELECT id, ordinal, raw_fields_json FROM disclosure_row_occurrences
                WHERE artifact_version_id = ?
                ORDER BY ordinal
                """,
                (version_id,),
            ).fetchall()
            if len(rows) != len(occurrences):
                raise ValueError("re-extraction changed the number of reported row occurrences")
            if any(
                json.loads(occurrence["raw_fields_json"]) != row
                for row, occurrence in zip(rows, occurrences, strict=True)
            ):
                raise ValueError(
                    "re-extraction changed reported row content or order; occurrence "
                    "correspondence is not established"
                )

            extraction_id = str(uuid.uuid4())
            extraction_status = (
                "partial" if any(not isinstance(row, dict) for row in rows) else "succeeded"
            )
            conn.execute(
                """
                INSERT INTO disclosure_extractions
                    (id, artifact_version_id, method, method_version, extracted_at,
                     status, representation_json, error)
                VALUES (?, ?, 'supporting-json', ?, ?, ?, ?, NULL)
                """,
                (
                    extraction_id,
                    version_id,
                    extraction_method_version,
                    extracted_at_ms,
                    extraction_status,
                    json.dumps(representation, separators=(",", ":"), sort_keys=True),
                ),
            )
            for row, occurrence in zip(rows, occurrences, strict=True):
                if isinstance(row, dict):
                    self._insert_normalization(
                        conn,
                        row_occurrence_id=occurrence["id"],
                        extraction_id=extraction_id,
                        row=row,
                        method_version=normalization_method_version,
                        normalized_at_ms=extracted_at_ms,
                    )

        return {
            "extractionId": extraction_id,
            "parseStatus": extraction_status,
            "rowOccurrencesCreated": 0,
        }

    @staticmethod
    def _insert_normalization(
        conn: sqlite3.Connection,
        *,
        row_occurrence_id: str,
        extraction_id: str,
        row: dict[str, Any],
        method_version: str,
        normalized_at_ms: int,
    ) -> None:
        if method_version == "1":
            strip_date_whitespace = False
        elif method_version == "2":
            strip_date_whitespace = True
        else:
            raise ValueError(f"unsupported normalization method version: {method_version}")

        normalized: dict[str, Any] = {}
        issues: list[str] = []

        ticker = row.get("ticker")
        if ticker is not None:
            if isinstance(ticker, str):
                normalized["ticker"] = ticker.strip().upper() or None
            else:
                issues.append("malformed_ticker")

        amount = row.get("amount") or row.get("amount_label")
        if amount is not None:
            if isinstance(amount, str):
                normalized["amount"] = amount.strip()
            else:
                issues.append("malformed_amount")

        parsed_dates: dict[str, date] = {}
        for source_key, output_key in (
            ("transaction_date", "transactionDate"),
            ("notification_date", "notificationDate"),
            ("disclosure_date", "disclosureDate"),
            ("filing_date", "filingDate"),
        ):
            raw_date = row.get(source_key)
            if raw_date is None or output_key in normalized:
                continue
            date_input = (
                raw_date.strip()
                if strip_date_whitespace and isinstance(raw_date, str)
                else raw_date
            )
            parsed_date = DisclosureApplication._parse_source_date(date_input)
            if parsed_date is None:
                issues.append(f"malformed_{source_key}")
                continue
            parsed_dates[output_key] = parsed_date
            normalized[output_key] = parsed_date.isoformat()

        if "transactionDate" in parsed_dates and "disclosureDate" in parsed_dates:
            latency = (parsed_dates["disclosureDate"] - parsed_dates["transactionDate"]).days
            normalized["disclosureLatencyDays"] = latency
            if latency < 0:
                issues.append("negative_disclosure_latency")

        status = "succeeded" if not issues else "partial"
        conn.execute(
            """
            INSERT INTO disclosure_normalizations
                (id, row_occurrence_id, extraction_id, method, method_version, normalized_at,
                 status, normalized_fields_json, issues_json)
            VALUES (?, ?, ?, 'disclosure-fields', ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                row_occurrence_id,
                extraction_id,
                method_version,
                normalized_at_ms,
                status,
                json.dumps(normalized, separators=(",", ":"), sort_keys=True),
                json.dumps(issues, separators=(",", ":")),
            ),
        )

    @staticmethod
    def _parse_source_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        for parser in (
            date.fromisoformat,
            lambda text: datetime.strptime(text, "%m/%d/%Y").date(),
            lambda text: datetime.strptime(text, "%m/%d/%y").date(),
        ):
            try:
                return parser(value)
            except ValueError:
                continue
        return None

    def _version_parse_status(self, version_id: str) -> str:
        with self._connection_factory() as conn:
            row = conn.execute(
                """
                SELECT status FROM disclosure_extractions
                WHERE artifact_version_id = ?
                ORDER BY extracted_at DESC, id DESC
                LIMIT 1
                """,
                (version_id,),
            ).fetchone()
        return row["status"] if row else "unsupported"

    def query_evidence(self, *, population: str) -> dict[str, Any]:
        with self._connection_factory() as conn:
            source_filing_rows = conn.execute(
                """
                SELECT id, source_name, source_filing_id, chamber, source_url,
                       discovered_at, raw_metadata_json
                FROM disclosure_source_filings
                WHERE population = ?
                ORDER BY discovered_at, source_name, source_filing_id
                """,
                (population,),
            ).fetchall()
            artifact_rows = conn.execute(
                """
                SELECT * FROM disclosure_artifacts
                WHERE population = ?
                ORDER BY created_at, id
                """,
                (population,),
            ).fetchall()
            artifacts = []
            for artifact in artifact_rows:
                versions = []
                version_rows = conn.execute(
                    """
                    SELECT id, content_sha256, content_length, media_type, first_observed_at
                    FROM disclosure_artifact_versions
                    WHERE artifact_id = ?
                    ORDER BY first_observed_at, id
                    """,
                    (artifact["id"],),
                ).fetchall()
                for version in version_rows:
                    row_occurrences = conn.execute(
                        """
                        SELECT r.id, r.source_filing_record_id, r.ordinal, r.raw_fields_json,
                               r.parse_status, f.source_name, f.source_filing_id AS source_identity
                        FROM disclosure_row_occurrences AS r
                        LEFT JOIN disclosure_source_filings AS f ON f.id = r.source_filing_record_id
                        WHERE artifact_version_id = ?
                        ORDER BY ordinal
                        """,
                        (version["id"],),
                    ).fetchall()
                    extractions = conn.execute(
                        """
                        SELECT id, method, method_version, extracted_at, status,
                               representation_json, error
                        FROM disclosure_extractions
                        WHERE artifact_version_id = ?
                        ORDER BY extracted_at, id
                        """,
                        (version["id"],),
                    ).fetchall()
                    serialized_rows = []
                    for row in row_occurrences:
                        normalization_rows = conn.execute(
                            """
                            SELECT id, extraction_id, method, method_version, normalized_at, status,
                                   normalized_fields_json, issues_json
                            FROM disclosure_normalizations
                            WHERE row_occurrence_id = ?
                            ORDER BY normalized_at, method_version, id
                            """,
                            (row["id"],),
                        ).fetchall()
                        serialized_rows.append(
                            {
                                "id": row["id"],
                                "sourceFiling": (
                                    {
                                        "id": row["source_filing_record_id"],
                                        "sourceName": row["source_name"],
                                        "sourceFilingId": row["source_identity"],
                                    }
                                    if row["source_filing_record_id"] is not None
                                    else None
                                ),
                                "ordinal": row["ordinal"],
                                "rawFields": json.loads(row["raw_fields_json"]),
                                "parseStatus": row["parse_status"],
                                "normalizations": [
                                    {
                                        "id": normalization["id"],
                                        "extractionId": normalization["extraction_id"],
                                        "method": normalization["method"],
                                        "methodVersion": normalization["method_version"],
                                        "normalizedAt": normalization["normalized_at"],
                                        "status": normalization["status"],
                                        "normalizedFields": json.loads(
                                            normalization["normalized_fields_json"]
                                        ),
                                        "issues": json.loads(normalization["issues_json"]),
                                    }
                                    for normalization in normalization_rows
                                ],
                            }
                        )
                    versions.append(
                        {
                            "id": version["id"],
                            "contentSha256": version["content_sha256"],
                            "contentLength": version["content_length"],
                            "mediaType": version["media_type"],
                            "firstObservedAt": version["first_observed_at"],
                            "extractions": [
                                {
                                    "id": row["id"],
                                    "method": row["method"],
                                    "methodVersion": row["method_version"],
                                    "extractedAt": row["extracted_at"],
                                    "status": row["status"],
                                    "representation": (
                                        json.loads(row["representation_json"])
                                        if row["representation_json"] is not None
                                        else None
                                    ),
                                    "error": row["error"],
                                }
                                for row in extractions
                            ],
                            "rowOccurrences": serialized_rows,
                        }
                    )

                observations = conn.execute(
                    """
                    SELECT id, artifact_version_id, observed_at, purpose,
                           availability_status, freshness_status, coverage_status,
                           http_status, source_metadata_json
                    FROM disclosure_retrieval_observations
                    WHERE artifact_id = ?
                    ORDER BY observed_at, id
                    """,
                    (artifact["id"],),
                ).fetchall()
                artifacts.append(
                    {
                        "id": artifact["id"],
                        "sourceName": artifact["source_name"],
                        "sourceAuthority": artifact["source_authority"],
                        "artifactKind": artifact["artifact_kind"],
                        "sourceUrl": artifact["source_url"],
                        "mediaType": artifact["media_type"],
                        "versions": versions,
                        "retrievalObservations": [
                            {
                                "id": row["id"],
                                "artifactVersionId": row["artifact_version_id"],
                                "observedAt": row["observed_at"],
                                "purpose": row["purpose"],
                                "availabilityStatus": row["availability_status"],
                                "freshnessStatus": row["freshness_status"],
                                "coverageStatus": row["coverage_status"],
                                "httpStatus": row["http_status"],
                                "sourceMetadata": json.loads(row["source_metadata_json"]),
                            }
                            for row in observations
                        ],
                    }
                )

            serialized_source_filings = []
            for row in source_filing_rows:
                evidence_rows = conn.execute(
                    """
                    SELECT e.artifact_version_id, e.extraction_id, e.source_record_key,
                           e.observed_at, x.method, x.method_version
                    FROM disclosure_source_filing_evidence AS e
                    JOIN disclosure_extractions AS x ON x.id = e.extraction_id
                    WHERE e.source_filing_record_id = ?
                    ORDER BY e.observed_at, e.id
                    """,
                    (row["id"],),
                ).fetchall()
                serialized_source_filings.append(
                    {
                        "id": row["id"],
                        "sourceName": row["source_name"],
                        "sourceFilingId": row["source_filing_id"],
                        "chamber": row["chamber"],
                        "sourceUrl": row["source_url"],
                        "discoveredAt": row["discovered_at"],
                        "rawMetadata": json.loads(row["raw_metadata_json"]),
                        "evidence": [
                            {
                                "artifactVersionId": evidence["artifact_version_id"],
                                "extractionId": evidence["extraction_id"],
                                "extractionMethod": evidence["method"],
                                "extractionMethodVersion": evidence["method_version"],
                                "sourceRecordKey": evidence["source_record_key"],
                                "observedAt": evidence["observed_at"],
                            }
                            for evidence in evidence_rows
                        ],
                    }
                )

        return {
            "population": population,
            "sourceFilings": serialized_source_filings,
            "artifacts": artifacts,
        }

    def query_chamber_readiness(self, *, population: str) -> dict[str, Any]:
        del population
        gate_codes = (
            "minimum_history_and_gaps",
            "original_artifact_retrieval",
            "amendment_and_backfill_behavior",
            "retention_permission",
            "daily_discovery",
            "downtime_catch_up",
            "older_additions_and_changes_reconciliation",
        )

        def unavailable(chamber: str) -> dict[str, Any]:
            return {
                "chamber": chamber,
                "availability": "unavailable",
                "reasonCode": "disclosure_source_validation_incomplete",
                "detail": (
                    f"{chamber.title()} disclosure readiness remains unavailable until every "
                    "approved source-validation gate has retained supporting evidence."
                ),
                "evaluatedAt": int(time.time() * 1000),
                "governingVersion": "signal-v2-disclosure-readiness-v1",
                "unmetPrerequisites": [
                    {"code": code, "supported": False} for code in gate_codes
                ],
            }

        return {"house": unavailable("house"), "senate": unavailable("senate")}

    def get_artifact_version(
        self,
        artifact_id: str,
        version_id: str,
        *,
        population: str,
    ) -> dict[str, Any]:
        with self._connection_factory() as conn:
            version = conn.execute(
                """
                SELECT v.id, v.content_sha256, v.raw_content, v.content_length,
                       v.media_type, v.first_observed_at
                FROM disclosure_artifact_versions AS v
                JOIN disclosure_artifacts AS a ON a.id = v.artifact_id
                WHERE a.id = ? AND v.id = ? AND a.population = ?
                """,
                (artifact_id, version_id, population),
            ).fetchone()
            if version is None:
                raise KeyError(version_id)
            extraction_rows = conn.execute(
                """
                SELECT id, method, method_version, extracted_at, status,
                       representation_json, error
                FROM disclosure_extractions
                WHERE artifact_version_id = ?
                ORDER BY extracted_at, id
                """,
                (version_id,),
            ).fetchall()
            observation_rows = conn.execute(
                """
                SELECT id, observed_at, purpose, availability_status,
                       freshness_status, coverage_status, http_status,
                       source_metadata_json
                FROM disclosure_retrieval_observations
                WHERE artifact_id = ? AND artifact_version_id = ?
                ORDER BY observed_at, id
                """,
                (artifact_id, version_id),
            ).fetchall()

        return {
            "id": version["id"],
            "contentSha256": version["content_sha256"],
            "contentLength": version["content_length"],
            "mediaType": version["media_type"],
            "firstObservedAt": version["first_observed_at"],
            "rawContent": bytes(version["raw_content"]),
            "extractions": [
                {
                    "id": row["id"],
                    "method": row["method"],
                    "methodVersion": row["method_version"],
                    "extractedAt": row["extracted_at"],
                    "status": row["status"],
                    "representation": (
                        json.loads(row["representation_json"])
                        if row["representation_json"] is not None
                        else None
                    ),
                    "error": row["error"],
                }
                for row in extraction_rows
            ],
            "retrievalObservations": [
                {
                    "id": row["id"],
                    "observedAt": row["observed_at"],
                    "purpose": row["purpose"],
                    "availabilityStatus": row["availability_status"],
                    "freshnessStatus": row["freshness_status"],
                    "coverageStatus": row["coverage_status"],
                    "httpStatus": row["http_status"],
                    "sourceMetadata": json.loads(row["source_metadata_json"]),
                }
                for row in observation_rows
            ],
        }
