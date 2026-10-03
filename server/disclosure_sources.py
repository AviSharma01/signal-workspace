from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


HOUSE_BASE_URL = "https://disclosures-clerk.house.gov/public_disc"
SAFE_METADATA_HEADERS = ("etag", "last-modified", "content-type")
SAFE_RETRIEVAL_METADATA_KEYS = (*SAFE_METADATA_HEADERS, "errorType")
HOUSE_SOURCE_TIMEZONE = ZoneInfo("America/New_York")


def current_house_report_year() -> int:
    return datetime.now(HOUSE_SOURCE_TIMEZONE).year


def validate_house_report_year(report_year: int) -> None:
    if report_year < 2008 or report_year > current_house_report_year():
        raise ValueError("House report year is outside the supported locator range")


def house_index_url(report_year: int) -> str:
    validate_house_report_year(report_year)
    return f"{HOUSE_BASE_URL}/financial-pdfs/{report_year}FD.ZIP"


def house_filing_url(report_year: int, document_id: str) -> str:
    validate_house_report_year(report_year)
    if not document_id.isdigit():
        raise ValueError("House document ID must contain only digits")
    return f"{HOUSE_BASE_URL}/ptr-pdfs/{report_year}/{document_id}.pdf"


@dataclass(frozen=True)
class FetchedSourceArtifact:
    source_url: str
    media_type: str
    content: bytes | None
    retrieved_at_ms: int
    http_status: int | None
    availability_status: str
    source_metadata: dict[str, Any]


class HouseDisclosureSource:
    def __init__(self, *, timeout_seconds: float = 30.0):
        self._timeout_seconds = timeout_seconds

    def fetch_index(self, report_year: int) -> FetchedSourceArtifact:
        return self._fetch(house_index_url(report_year))

    def fetch_filing(self, report_year: int, document_id: str) -> FetchedSourceArtifact:
        return self._fetch(house_filing_url(report_year, document_id))

    def _fetch(self, source_url: str) -> FetchedSourceArtifact:
        request = urllib.request.Request(
            source_url,
            headers={"User-Agent": "Signal disclosure evidence collector/2"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                content = response.read()
                headers = self._safe_headers(response.headers)
                return FetchedSourceArtifact(
                    source_url=source_url,
                    media_type=headers.get("content-type", "application/octet-stream").split(";", 1)[0],
                    content=content,
                    retrieved_at_ms=int(time.time() * 1000),
                    http_status=response.status,
                    availability_status="available",
                    source_metadata=headers,
                )
        except urllib.error.HTTPError as exc:
            headers = self._safe_headers(exc.headers)
            return FetchedSourceArtifact(
                source_url=source_url,
                media_type=headers.get("content-type", "application/octet-stream").split(";", 1)[0],
                content=exc.read(),
                retrieved_at_ms=int(time.time() * 1000),
                http_status=exc.code,
                availability_status="unavailable",
                source_metadata=headers,
            )
        except urllib.error.URLError as exc:
            return FetchedSourceArtifact(
                source_url=source_url,
                media_type="application/octet-stream",
                content=None,
                retrieved_at_ms=int(time.time() * 1000),
                http_status=None,
                availability_status="unavailable",
                source_metadata={"errorType": type(exc.reason).__name__},
            )

    @staticmethod
    def _safe_headers(headers: Any) -> dict[str, str]:
        lowered = {str(name).lower(): value for name, value in headers.items()}
        return {
            name: lowered[name]
            for name in SAFE_METADATA_HEADERS
            if name in lowered
        }
