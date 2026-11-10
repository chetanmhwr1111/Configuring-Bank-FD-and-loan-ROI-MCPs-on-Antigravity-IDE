from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from mcp.server.fastmcp import FastMCP

from .sources import BANKS, RBI_SOURCES

mcp = FastMCP("india-bank-rates")
CACHE_SECONDS = 15 * 60
_cache: dict[str, tuple[float, Any]] = {}
HEADERS = {
    "User-Agent": "IndiaBankRatesMCP/0.1 (informational rate comparison; contact: admin@example.invalid)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get(url: str, force: bool = False) -> str:
    if not force and url in _cache and time.time() - _cache[url][0] < CACHE_SECONDS:
        return _cache[url][1]
    with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text
    _cache[url] = (time.time(), html)
    return html


def _clean(value: Any) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _table_records(html: str) -> list[dict[str, str]]:
    """Extract HTML tables without assuming one fixed bank-specific schema."""
    try:
        tables = pd.read_html(StringIO(html))
    except (ValueError, ImportError):
        tables = []

    records: list[dict[str, str]] = []

    for table in tables:
        table.columns = [str(c) for c in table.columns]

        for _, row in table.iterrows():
            record = {
                str(k): _clean(v)
                for k, v in row.to_dict().items()
            }

            if any(v for v in record.values()):
                records.append(record)

    return records


def _flatten_page(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def _find_repo_rate(text: str) -> str | None:
    # Require "repo rate" near a percentage; avoid treating unrelated rates as repo.
    patterns = [
        r"(?:policy\s+)?repo\s+rate(?:\s+is|\s+at|:)?\s*(?:has been kept at|stands at|of)?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"repo rate.{0,100}?([0-9]+(?:\.[0-9]+)?)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                rate = float(match.group(1))
                if 0 < rate < 20:
                    return f"{rate:.2f}%"
            except ValueError:
                pass
    return None


def _normalize_row(bank: dict[str, str], row: dict[str, str], source_url: str) -> dict[str, Any]:
    joined = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
    # Keep original columns because bank table schemas vary widely.
    tenure = ""
    for key, value in row.items():
        if re.search(r"tenure|period|maturity|days|months|years|duration", key, re.I):
            tenure = value
            break
    rates = re.findall(r"(?<!\d)(\d{1,2}(?:\.\d{1,2})?)\s*%", joined)
    return {
        "bank": bank["name"],
        "category": bank["category"],
        "tenure": tenure,
        "rates_found": rates,
        "row": row,
        "source_url": source_url,
        "retrieved_at": _now(),
        "verification_note": "Automatically extracted from an official-source page; verify row labels and eligibility on the source page.",
    }


def _fetch_bank(bank: dict[str, str], force: bool = False) -> dict[str, Any]:
    try:
        html = _get(bank["url"], force=force)
        rows = _table_records(html)
        fd_rows = []
        for row in rows:
            joined = " ".join([*row.keys(), *row.values()])
            if re.search(r"fixed\s*deposit|\bFD\b|senior citizen|general public|deposit rate", joined, re.I):
                fd_rows.append(_normalize_row(bank, row, bank["url"]))
        if not fd_rows:
            return {
                "bank": bank["name"], "category": bank["category"], "source_url": bank["url"],
                "retrieved_at": _now(), "status": "no_matching_table_rows",
                "rows": [], "message": "Page fetched, but no likely FD table rows were detected. A bank-specific adapter may be needed."
            }
        return {
            "bank": bank["name"], "category": bank["category"], "source_url": bank["url"],
            "retrieved_at": _now(), "status": "ok", "rows": fd_rows
        }
    except Exception as exc:
        return {
            "bank": bank["name"], "category": bank["category"], "source_url": bank["url"],
            "retrieved_at": _now(), "status": "fetch_error",
            "rows": [], "message": f"{type(exc).__name__}: {exc}"
        }


@mcp.tool()
def get_repo_rate() -> dict[str, Any]:
    """Fetch the RBI policy repo rate from configured RBI pages; includes source and retrieval timestamp."""
    attempts = []
    for url in RBI_SOURCES:
        try:
            html = _get(url)
            text = _flatten_page(html)
            rate = _find_repo_rate(text)
            attempts.append({"source_url": url, "status": "rate_found" if rate else "rate_not_detected"})
            if rate:
                return {
                    "rate": rate,
                    "authority": "Reserve Bank of India",
                    "source_url": url,
                    "retrieved_at": _now(),
                    "status": "extracted",
                    "note": "Automatically detected from page text. Confirm the latest policy decision on RBI's official website."
                }
        except Exception as exc:
            attempts.append({"source_url": url, "status": "fetch_error", "message": str(exc)})
    return {
        "rate": None, "authority": "Reserve Bank of India", "retrieved_at": _now(),
        "status": "not_detected", "attempts": attempts,
        "message": "No repo rate could be confidently extracted from the configured pages. Update RBI_SOURCES or add an RBI-specific parser; no value was guessed."
    }


@mcp.tool()
def list_banks(category: str | None = None) -> list[dict[str, str]]:
    """List configured banks. category may be 'public' or 'private'."""
    cat = (category or "").strip().lower()
    banks = BANKS if not cat else [b for b in BANKS if b["category"] == cat]
    return [{"name": b["name"], "category": b["category"], "source_url": b["url"]} for b in banks]


@mcp.tool()
def get_fd_rates(
    bank_name: str | None = None,
    category: str | None = None,
    tenure: str | None = None,
    customer_type: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Fetch likely FD rate rows from configured bank pages and filter them.

    bank_name is a case-insensitive substring. category is public/private.
    tenure and customer_type are text filters applied to extracted row content.
    """
    chosen = BANKS
    if category:
        chosen = [b for b in chosen if b["category"] == category.strip().lower()]
    if bank_name:
        chosen = [b for b in chosen if bank_name.lower() in b["name"].lower()]
    results = [_fetch_bank(b, force=force_refresh) for b in chosen]
    flat_rows = []
    for result in results:
        for row in result.get("rows", []):
            blob = (row.get("tenure", "") + " " + " ".join(row.get("row", {}).values())).lower()
            if tenure and tenure.lower() not in blob:
                continue
            if customer_type and customer_type.lower() not in blob:
                continue
            flat_rows.append(row)
    return {
        "retrieved_at": _now(),
        "filters": {"bank_name": bank_name, "category": category, "tenure": tenure, "customer_type": customer_type},
        "banks_checked": len(chosen),
        "banks_with_rows": sum(1 for r in results if r.get("status") == "ok"),
        "bank_status": [{k: r.get(k) for k in ("bank", "category", "status", "source_url", "message")} for r in results],
        "rows": flat_rows,
        "note": "Rows are raw table extractions, not guaranteed normalized rate cards. Verify tenure, deposit amount, callable status, and customer eligibility at the official source."
    }


@mcp.tool()
def compare_fd_rates(
    tenure: str | None = None,
    customer_type: str = "general",
    category: str | None = None,
    limit: int = 10,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Compare detected FD rows, sorting rows with numeric percentage values first.

    Because bank table layouts differ, this is a best-effort comparison, not a guaranteed
    apples-to-apples ranking. Always inspect each row and source URL.
    """
    data = get_fd_rates(category=category, tenure=tenure, customer_type=customer_type, force_refresh=force_refresh)
    rows = data["rows"]
    for row in rows:
        numeric = []
        for rate in row.get("rates_found", []):
            try:
                numeric.append(float(rate))
            except ValueError:
                pass
        row["max_rate_found_percent"] = max(numeric) if numeric else None
    rows.sort(key=lambda r: r["max_rate_found_percent"] if r["max_rate_found_percent"] is not None else -1, reverse=True)
    return {
        "retrieved_at": data["retrieved_at"],
        "filters": data["filters"],
        "comparison_warning": "Best-effort ranking based on percentages found in table rows; a row may contain general and senior rates or multiple columns. Confirm comparable tenure and customer type before relying on ranking.",
        "results": rows[:max(1, min(limit, 100))],
        "banks_checked": data["banks_checked"],
        "bank_status": data["bank_status"],
    }


@mcp.tool()
def refresh_sources() -> dict[str, Any]:
    """Clear the in-memory cache so the next rate lookup fetches pages again."""
    _cache.clear()
    return {"status": "ok", "message": "Cache cleared. The next tool call will fetch sources again.", "cleared_at": _now()}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
