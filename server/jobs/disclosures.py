from __future__ import annotations

from typing import Iterable

from db.database import get_connection
from disclosure_sources import (
    FetchedSourceArtifact,
    HouseDisclosureSource,
    current_house_report_year,
)
from disclosures import DisclosureApplication, RetrievedArtifact


MINIMUM_COMPLETE_HISTORY_YEARS = 5
_application = DisclosureApplication(get_connection)
_source = HouseDisclosureSource()


def default_report_years(*, current_report_year: int | None = None) -> list[int]:
    current = current_report_year or current_house_report_year()
    return list(range(current - MINIMUM_COMPLETE_HISTORY_YEARS, current + 1))


def _ingest_index(
    fetched: FetchedSourceArtifact,
    *,
    report_year: int,
    purpose: str,
    application: DisclosureApplication,
) -> dict:
    return application.ingest_house_index(
        RetrievedArtifact.from_house_source(fetched, purpose=purpose),
        report_year=report_year,
    )


def _ingest_index_and_original_filings(
    *,
    report_year: int,
    purpose: str,
    application: DisclosureApplication,
    source: HouseDisclosureSource,
) -> list[dict]:
    index_result = _ingest_index(
        source.fetch_index(report_year),
        report_year=report_year,
        purpose=purpose,
        application=application,
    )
    results = [index_result]
    for document_id in index_result["filingDocumentIds"]:
        results.append(
            application.ingest_house_filing(
                RetrievedArtifact.from_house_source(
                    source.fetch_filing(report_year, document_id),
                    purpose=purpose,
                ),
                report_year=report_year,
                document_id=document_id,
            )
        )
    return results


def run_startup_disclosure_catch_up(
    *,
    application: DisclosureApplication = _application,
    source: HouseDisclosureSource = _source,
    report_years: Iterable[int] | None = None,
) -> list[dict]:
    years = list(report_years) if report_years is not None else default_report_years()
    results = []
    for report_year in years:
        results.extend(
            _ingest_index_and_original_filings(
                source=source,
                report_year=report_year,
                purpose="startup_catch_up",
                application=application,
            )
        )
    return results


def run_daily_disclosure_discovery(
    *,
    application: DisclosureApplication = _application,
    source: HouseDisclosureSource = _source,
    current_report_year: int | None = None,
    reconciliation_years: Iterable[int] | None = None,
) -> list[dict]:
    current = current_report_year or current_house_report_year()
    older_years = (
        list(reconciliation_years)
        if reconciliation_years is not None
        else default_report_years(current_report_year=current)[:-1]
    )
    results = _ingest_index_and_original_filings(
        source=source,
        report_year=current,
        purpose="daily_discovery",
        application=application,
    )
    for report_year in older_years:
        if report_year == current:
            continue
        results.extend(
            _ingest_index_and_original_filings(
                source=source,
                report_year=report_year,
                purpose="reconciliation",
                application=application,
            )
        )
    return results
