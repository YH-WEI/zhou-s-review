from __future__ import annotations

import itertools
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

import requests

from . import __version__
from .common import (
    FROZEN_DIR,
    REPO_ROOT,
    REVIEW_ROOT,
    load_yaml,
    normalize_doi,
    read_csv,
    sha256_file,
    utc_now,
    write_csv,
    write_json,
)


SEARCH_RUN_ID = "RUN_20260831_EVIDENCE_MAP_01"

SEARCH_LOG_FIELDS = [
    "search_run_id",
    "query_id",
    "query_family",
    "source_database",
    "exact_query",
    "request_url_redacted",
    "searched_at_utc",
    "date_start",
    "date_end",
    "filters",
    "sort_order",
    "page_or_cursor",
    "returned_count",
    "total_count",
    "execution_limit",
    "capped_or_truncated",
    "http_status",
    "retry_count",
    "raw_response_path",
    "raw_response_sha256",
    "software_version_or_commit",
    "notes",
]

CANDIDATE_FIELDS = [
    "search_record_id",
    "search_run_id",
    "query_id",
    "query_family",
    "source_database",
    "source_record_id",
    "rank_in_response",
    "title",
    "abstract",
    "publication_year",
    "doi_raw",
    "doi_normalized",
    "stable_url",
    "oa_url",
    "document_type",
    "authors",
    "venue_or_issuer",
    "language",
    "region_or_jurisdiction",
    "repository_path",
    "source_sha256",
    "raw_response_path",
]


@dataclass(frozen=True)
class Query:
    query_id: str
    family: str
    text: str


def _or_terms(terms: Iterable[str]) -> str:
    escaped = [f'"{term}"' if " " in term or "-" in term else term for term in terms]
    return "(" + " OR ".join(escaped) + ")"


def generate_queries(config: dict) -> list[Query]:
    assets = {value["code"]: _or_terms(value["terms"]) for value in config["assets"].values()}
    services = {key: _or_terms(value["terms"]) for key, value in config["services"].items()}
    coordination = _or_terms(config["coordination_terms"])
    evidence = _or_terms(config["evidence_terms"])
    queries: list[Query] = []

    for asset_code, asset_terms in assets.items():
        for service_code, service_terms in services.items():
            queries.append(
                Query(
                    f"QPR_{asset_code}_{service_code}",
                    "prior_reviews",
                    f"{asset_terms} AND {service_terms} AND (review OR perspective OR survey)",
                )
            )
            queries.append(
                Query(
                    f"QSA_{asset_code}_{service_code}",
                    "single_asset_service",
                    f"{asset_terms} AND {service_terms}",
                )
            )
            queries.append(
                Query(
                    f"QFIELD_{asset_code}_{service_code}",
                    "field_and_operational_evidence",
                    f"{asset_terms} AND {service_terms} AND {evidence}",
                )
            )

    for (asset_a, terms_a), (asset_b, terms_b) in itertools.combinations(assets.items(), 2):
        for service_code, service_terms in services.items():
            queries.append(
                Query(
                    f"QPAIR_{asset_a}_{asset_b}_{service_code}",
                    "pairwise_multi_asset",
                    f"{terms_a} AND {terms_b} AND {service_terms} AND {coordination}",
                )
            )

    multi_asset_terms = _or_terms(["multi-asset", "cross-sector", "integrated energy management", "virtual power plant"])
    all_focal_terms = "(" + " OR ".join(assets.values()) + ")"
    for service_code, service_terms in services.items():
        queries.append(
            Query(
                f"QMA_{service_code}",
                "three_plus_or_broad_multi_asset",
                f"{all_focal_terms} AND {multi_asset_terms} AND {service_terms} AND {coordination}",
            )
        )

    return sorted(queries, key=lambda query: query.query_id)


def _strip_markup(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def _crossref_year(item: dict) -> str:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def _crossref_candidates(query: Query, raw_rel: str, payload: dict) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, item in enumerate(payload.get("message", {}).get("items", []), start=1):
        authors = []
        for author in item.get("author", []):
            name = " ".join(part for part in (author.get("given", ""), author.get("family", "")) if part)
            if name:
                authors.append(name)
        links = item.get("link") or []
        oa_url = next((link.get("URL", "") for link in links if "application/pdf" in link.get("content-type", "")), "")
        rows.append(
            {
                "search_run_id": SEARCH_RUN_ID,
                "query_id": query.query_id,
                "query_family": query.family,
                "source_database": "crossref",
                "source_record_id": item.get("DOI") or item.get("URL", ""),
                "rank_in_response": rank,
                "title": " ".join(item.get("title") or []),
                "abstract": _strip_markup(item.get("abstract")),
                "publication_year": _crossref_year(item),
                "doi_raw": item.get("DOI", ""),
                "doi_normalized": normalize_doi(item.get("DOI")),
                "stable_url": item.get("URL", ""),
                "oa_url": oa_url,
                "document_type": item.get("type", ""),
                "authors": "|".join(authors),
                "venue_or_issuer": item.get("publisher", ""),
                "language": item.get("language", ""),
                "region_or_jurisdiction": "",
                "repository_path": "",
                "source_sha256": "",
                "raw_response_path": raw_rel,
            }
        )
    return rows


def _openalex_abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    tokens: list[tuple[int, str]] = []
    for word, positions in inverted.items():
        tokens.extend((int(position), word) for position in positions)
    return " ".join(word for _, word in sorted(tokens))


def _openalex_candidates(query: Query, raw_rel: str, payload: dict) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, item in enumerate(payload.get("results", []), start=1):
        authors = [entry.get("author", {}).get("display_name", "") for entry in item.get("authorships", [])]
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        oa = item.get("open_access") or {}
        rows.append(
            {
                "search_run_id": SEARCH_RUN_ID,
                "query_id": query.query_id,
                "query_family": query.family,
                "source_database": "openalex",
                "source_record_id": item.get("id", ""),
                "rank_in_response": rank,
                "title": item.get("display_name") or item.get("title", ""),
                "abstract": _openalex_abstract(item.get("abstract_inverted_index")),
                "publication_year": item.get("publication_year", ""),
                "doi_raw": item.get("doi", ""),
                "doi_normalized": normalize_doi(item.get("doi")),
                "stable_url": primary.get("landing_page_url") or item.get("id", ""),
                "oa_url": oa.get("oa_url") or primary.get("pdf_url", ""),
                "document_type": item.get("type", ""),
                "authors": "|".join(filter(None, authors)),
                "venue_or_issuer": source.get("display_name", ""),
                "language": item.get("language", ""),
                "region_or_jurisdiction": "",
                "repository_path": "",
                "source_sha256": "",
                "raw_response_path": raw_rel,
            }
        )
    return rows


def _request_json(
    session: requests.Session,
    url: str,
    params: dict[str, object],
    raw_path: Path,
    retries: list[int],
) -> tuple[dict, int, int, str, str]:
    if raw_path.exists():
        wrapper = json.loads(raw_path.read_text(encoding="utf-8"))
        return (
            wrapper["response"],
            int(wrapper["http_status"]),
            int(wrapper.get("retry_count", 0)),
            wrapper["retrieved_at_utc"],
            wrapper["request_url_redacted"],
        )
    last_error = ""
    for attempt in range(len(retries) + 1):
        try:
            response = session.get(url, params=params, timeout=60)
            request_url = response.url
            if response.status_code == 200:
                retrieved_at = utc_now()
                payload = response.json()
                wrapper = {
                    "http_status": response.status_code,
                    "request_url_redacted": re.sub(r"([?&](?:api_key|mailto)=)[^&]+", r"\1REDACTED", request_url),
                    "retrieved_at_utc": retrieved_at,
                    "retry_count": attempt,
                    "response": payload,
                }
                write_json(raw_path, wrapper)
                return payload, response.status_code, attempt, retrieved_at, wrapper["request_url_redacted"]
            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        if attempt < len(retries):
            time.sleep(retries[attempt])
    raise RuntimeError(f"Metadata request failed after retries: {last_error}")


def _repository_candidates(inventory: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    title_overrides = {
        "案例论文/s41560-025-01927-1(1).pdf": "AI data centres as grid-interactive assets",
    }
    for rank, row in enumerate(inventory, start=1):
        path = REPO_ROOT / row["repository_path"]
        title = title_overrides.get(row["repository_path"], path.stem)
        rows.append(
            {
                "search_run_id": SEARCH_RUN_ID,
                "query_id": "QREPO_SEEDS",
                "query_family": "repository_seeds",
                "source_database": "repository",
                "source_record_id": row["source_file_id"],
                "rank_in_response": rank,
                "title": title,
                "abstract": "",
                "publication_year": re.match(r"(?:March 18, )?(20\d{2})", title).group(1) if re.match(r"(?:March 18, )?(20\d{2})", title) else "",
                "doi_raw": "",
                "doi_normalized": "",
                "stable_url": "",
                "oa_url": "",
                "document_type": path.suffix.lower().lstrip("."),
                "authors": "",
                "venue_or_issuer": "",
                "language": "zh" if path.suffix.lower() == ".docx" else "en",
                "region_or_jurisdiction": "",
                "repository_path": row["repository_path"],
                "source_sha256": row["sha256"],
                "raw_response_path": "",
            }
        )
    return rows


def run_discovery(config_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    config = load_yaml(config_path)
    date_start = config["date_bounds"]["start"]
    date_end = config["date_bounds"]["end"]
    retrieval = config["retrieval"]
    limit = min(int(retrieval["execution_records_per_query"]), int(retrieval["max_records_per_query"]))
    retries = [int(value) for value in retrieval["backoff_seconds"]][: int(retrieval["max_retries"])]
    queries = generate_queries(config)
    if len(queries) != 95:
        raise RuntimeError(f"Expected 95 enabled query-family instances, generated {len(queries)}")

    session = requests.Session()
    contact = os.environ.get(config["sources"]["crossref"]["contact_email_env"], "")
    session.headers.update(
        {
            "User-Agent": f"zhou-review-evidence-map/{__version__} (https://github.com/YH-WEI/zhou-s-review; contact={contact or 'not-supplied'})",
            "Accept": "application/json",
        }
    )
    raw_root = REVIEW_ROOT / retrieval["raw_metadata_directory"]
    search_log: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []

    inventory = read_csv(REVIEW_ROOT / "data" / "source_inventory.csv")
    repository_rows = _repository_candidates(inventory)
    candidates.extend(repository_rows)
    search_log.append(
        {
            "search_run_id": SEARCH_RUN_ID,
            "query_id": "QREPO_SEEDS",
            "query_family": "repository_seeds",
            "source_database": "repository",
            "exact_query": "Inventory all pre-existing repository PDF/DOCX source files",
            "request_url_redacted": "not_applicable",
            "searched_at_utc": utc_now(),
            "date_start": date_start,
            "date_end": date_end,
            "filters": "repository presence is not inclusion",
            "sort_order": "repository_path ascending",
            "page_or_cursor": "not_applicable",
            "returned_count": len(repository_rows),
            "total_count": len(repository_rows),
            "execution_limit": len(repository_rows),
            "capped_or_truncated": "no",
            "http_status": "not_applicable",
            "retry_count": 0,
            "raw_response_path": "not_applicable",
            "raw_response_sha256": "not_applicable",
            "software_version_or_commit": __version__,
            "notes": "Local immutable source inventory.",
        }
    )

    source_specs = []
    if config["sources"]["crossref"]["enabled"]:
        source_specs.append("crossref")
    if config["sources"]["openalex"]["enabled"]:
        source_specs.append("openalex")

    for source in source_specs:
        for index, query in enumerate(queries, start=1):
            raw_path = raw_root / source / f"{query.query_id}.json"
            if source == "crossref":
                url = config["sources"]["crossref"]["base_url"].rstrip("/") + "/works"
                params: dict[str, object] = {
                    "query.bibliographic": query.text,
                    "filter": f"from-pub-date:{date_start},until-pub-date:{date_end}",
                    "rows": limit,
                    "sort": "relevance",
                    "order": "desc",
                }
                if contact:
                    params["mailto"] = contact
            else:
                url = config["sources"]["openalex"]["base_url"].rstrip("/") + "/works"
                params = {
                    "search": query.text,
                    "filter": f"from_publication_date:{date_start},to_publication_date:{date_end}",
                    "per-page": limit,
                    "sort": "relevance_score:desc",
                    "select": "id,doi,title,display_name,publication_year,publication_date,type,authorships,primary_location,open_access,language,abstract_inverted_index",
                }
                api_key = os.environ.get(config["sources"]["openalex"]["api_key_env"], "")
                if api_key:
                    params["api_key"] = api_key

            payload, status, retry_count, retrieved_at, request_url = _request_json(
                session, url, params, raw_path, retries
            )
            raw_rel = raw_path.relative_to(REVIEW_ROOT).as_posix()
            if source == "crossref":
                message = payload.get("message", {})
                total = int(message.get("total-results", 0))
                returned = len(message.get("items", []))
                new_rows = _crossref_candidates(query, raw_rel, payload)
            else:
                meta = payload.get("meta", {})
                total = int(meta.get("count", 0))
                returned = len(payload.get("results", []))
                new_rows = _openalex_candidates(query, raw_rel, payload)
            candidates.extend(new_rows)
            search_log.append(
                {
                    "search_run_id": SEARCH_RUN_ID,
                    "query_id": query.query_id,
                    "query_family": query.family,
                    "source_database": source,
                    "exact_query": query.text,
                    "request_url_redacted": request_url,
                    "searched_at_utc": retrieved_at,
                    "date_start": date_start,
                    "date_end": date_end,
                    "filters": f"publication date {date_start} through {date_end}",
                    "sort_order": "relevance descending",
                    "page_or_cursor": "page 1",
                    "returned_count": returned,
                    "total_count": total,
                    "execution_limit": limit,
                    "capped_or_truncated": "yes" if total > returned else "no",
                    "http_status": status,
                    "retry_count": retry_count,
                    "raw_response_path": raw_rel,
                    "raw_response_sha256": sha256_file(raw_path),
                    "software_version_or_commit": __version__,
                    "notes": retrieval["execution_cap_reason"],
                }
            )
            if index % 10 == 0 or index == len(queries):
                print(f"discover {source}: {index}/{len(queries)} queries")
            time.sleep(0.05)

    manual_path = REVIEW_ROOT / config["sources"]["manual_imports"]["path"]
    manual_files = [path for path in manual_path.glob("*") if path.is_file()]
    search_log.append(
        {
            "search_run_id": SEARCH_RUN_ID,
            "query_id": "QMANUAL_IMPORTS",
            "query_family": "manual_imports",
            "source_database": "manual_imports",
            "exact_query": "Scan data/manual_imports for RIS/BibTeX/CSV exports",
            "request_url_redacted": "not_applicable",
            "searched_at_utc": utc_now(),
            "date_start": date_start,
            "date_end": date_end,
            "filters": "ris|bib|bibtex|csv",
            "sort_order": "filename ascending",
            "page_or_cursor": "not_applicable",
            "returned_count": len(manual_files),
            "total_count": len(manual_files),
            "execution_limit": "not_applicable",
            "capped_or_truncated": "no",
            "http_status": "not_applicable",
            "retry_count": 0,
            "raw_response_path": "not_applicable",
            "raw_response_sha256": "not_applicable",
            "software_version_or_commit": __version__,
            "notes": "No credentialed database export was supplied." if not manual_files else "Manual imports require provenance parsing.",
        }
    )

    for index, row in enumerate(candidates, start=1):
        row["search_record_id"] = f"R{index:06d}"
    write_csv(FROZEN_DIR / "search_log.csv", SEARCH_LOG_FIELDS, search_log)
    write_csv(FROZEN_DIR / "candidate_records.csv", CANDIDATE_FIELDS, candidates)
    return search_log, candidates
