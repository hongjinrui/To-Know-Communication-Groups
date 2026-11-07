#!/usr/bin/env python3
"""Collect author-matched arXiv candidates; never assert group attribution or edit logs.

Only Python's standard library is required. See docs/UPDATES.md for the review
contract. Failed groups retain their cache and last successful check timestamp.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
TERMS = re.compile(
    r"\b(wireless|communication[s]?|mimo|beamform\w*|antenna[s]?|channel[s]?|"
    r"radio|terahertz|millimeter|mmwave|ofdm|ris|reconfigurable|metasurface[s]?|"
    r"satellite[s]?|cellular|uplink|downlink|backscatter|isac|6g|5g|"
    r"spectrum|transceiver[s]?|modulation|coding|network[s]?|sensing|"
    r"federated|over.the.air|optical|localization)\b", re.I
)
ID_PATTERN = re.compile(r"^(?P<id>(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7}))(?:v(?P<version>\d+))?$", re.I)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def norm_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z]+", text.casefold()))


def full_name(name: str) -> bool:
    parts = norm_name(name).split()
    return len(parts) >= 2 and all(len(p) > 1 for p in parts)


def parse_feed(xml: str) -> list[dict]:
    root = ET.fromstring(xml)
    if root.tag != ATOM + "feed":
        raise ValueError("Response is not an Atom feed")
    entries = []
    for entry in root.findall(ATOM + "entry"):
        raw_id = (entry.findtext(ATOM + "id") or "").strip()
        if "api/errors" in raw_id:
            raise ValueError("arXiv returned an API error entry")
        match = ID_PATTERN.fullmatch(raw_id.split("/abs/")[-1])
        if not match:
            raise ValueError("arXiv entry contains an unrecognized paper ID")
        authors, affiliations = [], []
        for author in entry.findall(ATOM + "author"):
            name = " ".join((author.findtext(ATOM + "name") or "").split())
            if name:
                authors.append(name)
                affiliations.extend(x.text.strip() for x in author.findall(ARXIV + "affiliation") if x.text)
        title = " ".join((entry.findtext(ATOM + "title") or "").split())
        if not title or not authors:
            raise ValueError("Incomplete arXiv entry")
        paper_id = match.group("id")
        entries.append({
            "id": paper_id,
            "version": int(match.group("version") or 1),
            "title": title,
            "url": "https://arxiv.org/abs/" + paper_id,
            "published": entry.findtext(ATOM + "published") or "",
            "updated": entry.findtext(ATOM + "updated") or "",
            "authors": authors,
            "affiliations": sorted(set(affiliations)),
            "summary": " ".join((entry.findtext(ATOM + "summary") or "").split())[:6000],
        })
    return entries


def feed_total(xml: str) -> int | None:
    text = ET.fromstring(xml).findtext(OPENSEARCH + "totalResults")
    return int(text) if text is not None else None


def candidate(paper: dict, group: dict) -> dict | None:
    allowed = {norm_name(name) for name in group.get("authorQueries", []) if full_name(name)}
    matched = sorted({author for author in paper["authors"] if norm_name(author) in allowed})
    if not matched or not TERMS.search(paper["title"]):
        return None
    return {
        "groupId": group["id"],
        "matchedAuthors": matched,
        "reason": "英文全名精确匹配且标题含通信相关词；同名、单位与组归属仍需核实",
    }


def merge_candidates(cache: dict, groups: list[dict], results: dict, now: str) -> tuple[dict, dict]:
    output = copy.deepcopy(cache)
    output.setdefault("schemaVersion", 1)
    output.setdefault("papers", [])
    output.setdefault("baselineEstablishedAt", None)
    index = {paper["id"]: paper for paper in output["papers"]}
    checks = []
    new_count = revised_count = success_count = complete_count = 0
    group_baselines = output.setdefault("groupBaselines", {})
    for group in groups:
        gid = group["id"]
        result = results.get(gid, {"error": "No result was supplied"})
        if result.get("error"):
            checks.append({
                "groupId": gid, "state": "error", "records": 0,
                "error": result["error"], "attempted": result.get("attempted", True),
                **({"skipReason": result["skipReason"]} if result.get("skipReason") else {}),
            })
            continue
        try:
            parsed = parse_feed(result["xml"])
            returned_count = len(parsed)
            total_results = result.get("totalResults", feed_total(result["xml"]))
            if result.get("cutoff"):
                parsed = [paper for paper in parsed if paper["updated"] >= result["cutoff"]]
        except (ValueError, ET.ParseError, KeyError) as error:
            checks.append({"groupId": gid, "state": "error", "records": 0, "error": str(error)})
            continue
        success_count += 1
        first_group_check = gid not in group_baselines
        matching = 0
        for paper in parsed:
            evidence = candidate(paper, group)
            if evidence is None:
                continue
            matching += 1
            existing = index.get(paper["id"])
            if existing is None:
                existing = {
                    **paper,
                    "candidateStatus": "pending",
                    "groupIds": [],
                    "matchEvidence": [],
                    "firstSeenAt": now,
                    "lastSeenAt": now,
                    "changeType": "baseline" if first_group_check else "new",
                    "versions": [paper["version"]],
                }
                index[paper["id"]] = existing
                if not first_group_check:
                    new_count += 1
            elif paper["version"] > existing.get("version", 1):
                review_fields = [key for key in existing if key.startswith("review")]
                if existing.get("candidateStatus") in {"verified", "rejected"} or review_fields:
                    previous_review = {
                        "version": existing.get("version", 1),
                        "candidateStatus": existing.get("candidateStatus", "pending"),
                        **{key: existing[key] for key in review_fields},
                    }
                    existing.setdefault("previousReviews", []).append(previous_review)
                    existing["previousReview"] = previous_review
                for key in review_fields:
                    existing.pop(key, None)
                existing.update(paper)
                existing["changeType"] = "revision"
                existing["candidateStatus"] = "pending"
                existing["revisionSeenAt"] = now
                revised_count += 1
            existing["versions"] = sorted(set(existing.get("versions", [existing.get("version", 1)])) | {paper["version"]})
            existing["lastSeenAt"] = now
            if gid not in existing["groupIds"]:
                existing["groupIds"].append(gid)
            # A coauthored paper is stored once, with independent group evidence.
            existing["matchEvidence"] = [x for x in existing["matchEvidence"] if x["groupId"] != gid] + [evidence]
            existing["groupIds"].sort()
        group_baselines.setdefault(gid, now)
        check = {
            "groupId": gid, "state": "ok", "records": matching,
            "fetchedRecords": returned_count, "windowRecords": len(parsed),
            "sourceTotalResults": total_results,
            "historicalResultsTruncated": total_results is not None and total_results > returned_count,
            "coverageScope": "recent_updated_window" if result.get("cutoff") else "fixture",
            "windowCutoff": result.get("cutoff"),
            "windowComplete": not bool(result.get("coverageWarning")),
            "lastSuccessAt": now,
        }
        if result.get("coverageWarning"):
            check.update({"state": "partial", "warning": result["coverageWarning"]})
        else:
            complete_count += 1
        checks.append(check)
    if success_count and output["baselineEstablishedAt"] is None:
        output["baselineEstablishedAt"] = now
    output["papers"] = sorted(index.values(), key=lambda p: (p.get("published", ""), p["id"]), reverse=True)
    state = "ok" if complete_count == len(groups) and groups else "partial" if success_count else "error"
    status = {
        "schemaVersion": 1,
        "state": state,
        "lastAttemptAt": now,
        "lastSuccessAt": now if state == "ok" else None,
        "candidateCount": sum(p.get("candidateStatus") == "pending" for p in output["papers"]),
        "newCandidates": new_count,
        "revisedCandidates": revised_count,
        "groups": checks,
        "coverageScope": "最近更新时间窗口；不代表全历史论文",
        "message": "近期采集窗口完成；候选需审阅，不代表已确认组进展或全历史论文。" if state == "ok" else "采集未全部完成；旧数据已保留，未把失败解释为无更新。",
    }
    return output, status


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else copy.deepcopy(default)


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def fetch_group(group: dict, days: int, limit: int, attempts: int = 3) -> dict:
    names = [name for name in group.get("authorQueries", []) if full_name(name)]
    if not names:
        return {"error": "No eligible full-name author query"}
    # Sort by lastUpdatedDate so revisions of old preprints remain discoverable.
    # Apply the cutoff locally: the current manual documents submittedDate as
    # the date-range query field, which would lose revisions of older papers.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds").replace("+00:00", "Z")
    clauses = [f'au:"{re.sub(chr(34), "", name)}"' for name in names]
    query = "(" + " OR ".join(clauses) + ")"
    url = "https://export.arxiv.org/api/query?" + urlencode({
        "search_query": query, "start": 0, "max_results": limit,
        "sortBy": "lastUpdatedDate", "sortOrder": "descending",
    })
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": "CommunicationGroupAtlas/1.0 (research metadata; GitHub Actions)"})
            with urlopen(request, timeout=20) as response:
                xml = response.read(4 * 1024 * 1024 + 1)
            if len(xml) > 4 * 1024 * 1024:
                return {"error": "arXiv response exceeded 4 MiB"}
            decoded = xml.decode("utf-8")
            parsed = parse_feed(decoded)
            total = feed_total(decoded)
            result = {"xml": decoded, "cutoff": cutoff, "totalResults": total}
            could_have_more = total > len(parsed) if total is not None else len(parsed) >= limit
            if could_have_more and (not parsed or all(paper["updated"] >= cutoff for paper in parsed)):
                result["coverageWarning"] = "达到单组返回上限，窗口内可能有遗漏；需补查或提高limit"
            return result
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, OSError, ValueError, ET.ParseError) as error:
            if attempt == attempts - 1:
                return {"error": f"{type(error).__name__}: {str(error)[:200]}"}
            time.sleep(4 * (attempt + 1))
    return {"error": "No response"}


def run(data_dir: Path, fixture: Path | None = None, days: int = 45, limit: int = 80, delay: float = 3.1, budget_seconds: float = 20 * 60) -> dict:
    group_document = read_json(data_dir / "groups.json", [])
    groups = group_document.get("groups", []) if isinstance(group_document, dict) else group_document
    if not groups:
        raise ValueError("groups.json contains no groups")
    old_status = read_json(data_dir / "status.json", {})
    cache = read_json(data_dir / "papers.json", {"schemaVersion": 1, "papers": [], "baselineEstablishedAt": None})
    if fixture:
        fixture_data = read_json(fixture, {})
        now = fixture_data.get("now", utcnow())
        results = fixture_data.get("results", {})
    else:
        now = utcnow()
        results = {}
        consecutive_failures = 0
        deadline = time.monotonic() + budget_seconds

        def skip_for_budget(group_id: str) -> bool:
            if time.monotonic() < deadline:
                return False
            results[group_id] = {
                "error": "未尝试：本轮采集时间预算已用尽，保留旧数据",
                "attempted": False, "skipReason": "time_budget",
            }
            return True

        for i, group in enumerate(groups):
            if skip_for_budget(group["id"]):
                continue
            if consecutive_failures >= 3:
                results[group["id"]] = {
                    "error": "未尝试：连续三组采集失败，暂停本轮请求并保留旧数据",
                    "attempted": False, "skipReason": "consecutive_failures",
                }
                continue
            if i:
                time.sleep(max(3.1, delay))
                if skip_for_budget(group["id"]):
                    continue
            results[group["id"]] = fetch_group(group, days, limit)
            consecutive_failures = consecutive_failures + 1 if "error" in results[group["id"]] else 0
            print(f"{group['id']}: {'error' if 'error' in results[group['id']] else 'fetched'}", flush=True)
    output, status = merge_candidates(cache, groups, results, now)
    if status["state"] != "ok":
        status["lastSuccessAt"] = old_status.get("lastSuccessAt")
    previous_checks = {x["groupId"]: x for x in old_status.get("groups", [])}
    for check in status["groups"]:
        if check["state"] != "ok":
            check["lastSuccessAt"] = previous_checks.get(check["groupId"], {}).get("lastSuccessAt")
    # A total failure must leave the papers cache byte-for-byte unchanged.
    if status["state"] != "error":
        write_json(data_dir / "papers.json", output)
    write_json(data_dir / "status.json", status)
    # Deliberately never write data/updates.json: that file is editorial evidence.
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--fixture", type=Path, help="Offline fixture JSON with now/results mapping (xml or error)")
    parser.add_argument("--days", type=int, default=45)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--delay", type=float, default=3.1)
    parser.add_argument("--budget-seconds", type=float, default=20 * 60, help="Whole-round budget before starting another group (default: 1200)")
    args = parser.parse_args()
    if args.days < 1 or not 1 <= args.limit <= 2000 or args.budget_seconds <= 0:
        parser.error("--days and --budget-seconds must be positive; --limit must be between 1 and 2000")
    try:
        status = run(args.data_dir, args.fixture, args.days, args.limit, args.delay, args.budget_seconds)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({key: status[key] for key in ["state", "candidateCount", "newCandidates", "revisedCandidates"]}, ensure_ascii=False))
    # API outages are recorded and published without erasing the last good site.
    # CLI exits 0 for a recorded outage; structural/configuration errors exit 1.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
