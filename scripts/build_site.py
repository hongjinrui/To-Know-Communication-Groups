#!/usr/bin/env python3
"""Copy only public site files to dist (no research scratch files or credentials)."""
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def build():
    for filename in ("index.html", "styles.css", "app.js"):
        if not (ROOT / filename).is_file():
            raise ValueError(f"Missing public site file: {filename}")
    for filename in ("groups.json", "schools.json", "updates.json", "papers.json", "status.json"):
        json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data/groups.json").read_text(encoding="utf-8"))
    school_ids = [school["id"] for school in catalog["schools"]]
    group_ids = [group["id"] for group in catalog["groups"]]
    if len(set(school_ids)) != len(school_ids) or len(set(group_ids)) != len(group_ids):
        raise ValueError("Duplicate school or group ID")
    for group in catalog["groups"]:
        if group["schoolId"] not in school_ids:
            raise ValueError(f"Unknown school: {group['id']}")
        if not group.get("sources") or not group.get("leaders"):
            raise ValueError(f"Group lacks evidence or leaders: {group['id']}")
        for source in group.get("sources", []) + group.get("papers", []):
            parsed = urlsplit(source["url"])
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise ValueError(f"Invalid evidence URL: {group['id']}")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for filename in ("index.html", "styles.css", "app.js"):
        shutil.copy2(ROOT / filename, DIST / filename)
    for dirname in ("assets", "data"):
        source = ROOT / dirname
        if source.exists():
            shutil.copytree(source, DIST / dirname)
    (DIST / ".nojekyll").touch()
    print(f"Static site packaged: {DIST}")


if __name__ == "__main__":
    build()
