"""Native-text extraction for the measured House electronic PTR table layout.

Version 1: eight labeled columns, page/table/band occurrence positions. PDF text
and cell text are retained verbatim; font-decoding defects are never repaired.
Scans and unrecognized layouts remain unavailable. See the fixture manifest.
"""
from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from typing import Any

import pdfplumber


METHOD = "house-ptr-native-table"
VERSION = "1"
FIELDS = (
    "reported_id", "owner", "asset", "transaction_type", "transaction_date",
    "notification_date", "amount", "capital_gains_text",
)
HEADERS = ("id", "owner", "asset", "transactiontype", "date", "notificationdate", "amount", "cap.gains>$200?")


def _text(words: list[dict[str, Any]]) -> str:
    lines: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if not lines or abs(word["top"] - lines[-1][0]["top"]) > 3:
            lines.append([])
        lines[-1].append(word)
    return "\n".join(" ".join(w["text"] for w in sorted(line, key=lambda w: w["x0"])) for line in lines)


def _in_box(words: list[dict], box: tuple) -> list[dict]:
    x0, top, x1, bottom = box
    return [w for w in words if x0 <= (w["x0"] + w["x1"]) / 2 < x1
            and top <= (w["top"] + w["bottom"]) / 2 < bottom]


def extract_ptr(content: bytes) -> dict[str, Any]:
    representation: dict[str, Any] = {
        "engine": f"pdfplumber@{pdfplumber.__version__}",
        "pages": [], "rows": [], "unresolvedFragments": [], "issues": [],
    }
    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page_number, page in enumerate(pdf.pages, 1):
                words = page.extract_words(x_tolerance=2, y_tolerance=3)
                page_text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                page_rep = {"page": page_number, "width": page.width, "height": page.height,
                            "text": page_text, "words": words, "status": "unsupported"}
                representation["pages"].append(page_rep)
                if not page.chars:
                    representation["issues"].append(f"page_{page_number}:no_native_text")
                    continue
                header_groups: dict[tuple, list[dict]] = {}
                for rect in page.rects:
                    if rect["height"] > 20 and rect["width"] > 5 and rect["fill"]:
                        header_groups.setdefault((round(rect["top"], 2), round(rect["bottom"], 2)), []).append(rect)
                tables = []
                for rects in header_groups.values():
                    cells = [(r["x0"], r["top"], r["x1"], r["bottom"]) for r in sorted(rects, key=lambda r: r["x0"])]
                    labels = tuple(re.sub(r"\s", "", _text(_in_box(words, cell))).lower() for cell in cells)
                    if labels == HEADERS:
                        tables.append(cells)
                if not tables:
                    if representation["rows"] and ("Digitally Signed:" in page_text or "(owner:" in page_text.lower()):
                        page_rep["status"] = "ancillary"
                    else:
                        representation["issues"].append(f"page_{page_number}:unrecognized_layout")
                    continue
                page_rep["status"] = "parsed"
                for table_index, cells in enumerate(tables):
                    left, _, _, start = cells[0]
                    right = cells[-1][2]
                    # Electronic PTRs draw separate side-border segments for each
                    # transaction and supplementary-text band, even on white rows.
                    borders = [r for r in page.rects if r["width"] < 2 and r["height"] >= 8
                               and abs(r["x0"] - left) < 1 and r["bottom"] > start]
                    groups: dict[tuple[float, float], list[dict]] = {}
                    for word in words:
                        middle = (word["top"] + word["bottom"]) / 2
                        if middle < start or not left <= word["x0"] < right:
                            continue
                        spans = [r for r in borders if r["top"] <= middle < r["bottom"]]
                        if spans:
                            # On continuation pages the later-painted body border
                            # supersedes the overlapping repeated-header border.
                            border = spans[-1]
                            key = (max(start, border["top"]), border["bottom"])
                            groups.setdefault(key, []).append(word)
                    for band_index, ((top, end), band_words) in enumerate(sorted(groups.items())):
                        if not band_words:
                            continue
                        text = _text(band_words)
                        label = text.split("\n", 1)[0].replace("\x00", "").lower()
                        supplemental = re.match(r"^(filing status|f s|subholding of|s o|description|d)\s*:", label)
                        if supplemental:
                            # Full page text preserves all supplementary material.
                            # Do not reinterpret source "Amended" labels as relationships.
                            continue
                        row = {
                            field: _text(_in_box(band_words, (cell[0], top, cell[2], end)))
                            for field, cell in zip(FIELDS, cells, strict=True)
                        }
                        row["sourcePosition"] = {
                            "page": page_number, "table": table_index, "band": band_index,
                            "bbox": [round(left, 3), round(top, 3), round(right, 3), round(end, 3)],
                        }
                        row["text"] = text
                        if page_number > 1 and band_index == 0 and not any(
                            row[field] for field in ("transaction_type", "transaction_date", "notification_date")
                        ):
                            representation["unresolvedFragments"].append(row)
                            representation["issues"].append(f"page_{page_number}:unresolved_continuation")
                            if representation["rows"]:
                                previous = representation["rows"][-1]
                                previous["issues"].append("possibly_incomplete_at_page_break")
                                previous["parseStatus"] = "partial"
                            continue
                        row["issues"] = [f"missing_{field}" for field in
                                         ("asset", "transaction_type", "transaction_date", "notification_date", "amount")
                                         if not row[field]]
                        if "\x00" in "".join(row[field] for field in FIELDS[:7]):
                            row["issues"].append("undecodable_transaction_text")
                        row["parseStatus"] = "partial" if row["issues"] else "parsed"
                        representation["rows"].append(row)
    except Exception as exc:
        # Parser failures are retained as explicit outcomes, never as raw loss.
        representation["issues"].append(f"pdf_read_error:{type(exc).__name__}")
        return {"status": "partial" if representation["rows"] else "failed",
                "representation": representation}
    rows = representation["rows"]
    status = "succeeded" if rows else "unsupported"
    if rows and (representation["issues"] or any(r["parseStatus"] == "partial" for r in rows)):
        status = "partial"
    return {"status": status, "representation": representation}


def normalize_ptr_row(row: dict[str, Any]) -> tuple[dict, list[str]]:
    """house-ptr-fields@1. Only literal field normalization; no entity resolution."""
    normalized: dict[str, Any] = {}
    issues = []
    for key, output in (("transaction_date", "transactionDate"), ("notification_date", "notificationDate")):
        value = row.get(key, "")
        if value:
            try:
                normalized[output] = datetime.strptime(value, "%m/%d/%Y").date().isoformat()
            except ValueError:
                issues.append(f"malformed_{key}")
    direction = row.get("transaction_type", "")
    if direction in {"P", "S", "S (partial)", "S (full)", "E"}:
        normalized["transactionDirection"] = {"P": "purchase", "E": "exchange"}.get(direction, "sale")
    elif direction:
        issues.append("unrecognized_transaction_type")
    amount = " ".join(row.get("amount", "").split())
    money = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
    match = re.fullmatch(rf"\$({money}) - \$({money})", amount)
    if match:
        lower, upper = (int(value.replace(",", "")) for value in match.groups())
        if lower <= upper:
            normalized.update(amountLower=lower, amountUpper=upper)
        else:
            issues.append("reversed_amount_range")
    elif amount:
        issues.append("unresolved_amount")
    return normalized, issues
