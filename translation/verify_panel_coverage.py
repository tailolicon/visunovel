#!/usr/bin/env python3
"""Independent evidence-coverage audit; never reads or stores comic images."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GRADES = {
    "manhwa_vi_panel": "panel_observed",
    "manhwa_english_chapter_title": "chapter_title_observed",
    "novel_english_secondary": "chapter_text_observed",
}

def check(ledger: dict) -> list[str]:
    problems: list[str] = []
    observations = ledger.get("observations", [])
    panels = []
    seen_ids = set()
    for i, row in enumerate(observations):
        medium = row.get("medium")
        if row.get("id") in seen_ids:
            problems.append(f"observation {i}: duplicate id")
        seen_ids.add(row.get("id"))
        chapter = row.get("chapter")
        if type(chapter) is not int or not 1 <= chapter <= 20:
            problems.append(f"observation {i}: outside chapters 1-20")
        if medium not in EXPECTED_GRADES or row.get("evidence_grade") != EXPECTED_GRADES.get(medium):
            problems.append(f"observation {i}: medium and evidence grade disagree")
        if medium == "manhwa_vi_panel":
            panels.append(row)
            if row.get("approval") not in {"scene_only", "candidate"}:
                problems.append(f"observation {i}: Vietnamese panel does not authorize canon")
        elif row.get("approval") in {"scene_only", "approved", "editorial_approved"}:
            problems.append(f"observation {i}: secondary source cannot approve Vietnamese dialogue")
    image_urls = {p.get("source_url") for p in panels if p.get("source_url")}
    chapters = sorted({p["chapter"] for p in panels if type(p.get("chapter")) is int})
    claimed = ledger.get("covered_vn_manhwa_panels", {})
    if claimed.get("chapters") != chapters or claimed.get("panel_count") != len(image_urls):
        problems.append("claimed panel coverage differs from inspected unique image URLs")
    if ledger.get("editorial_release_gate") != "NOT_READY_FOR_CANON_LOCK":
        problems.append("unreviewed evidence must not unlock canon")
    return problems

def main() -> int:
    data = json.loads((ROOT / "translation/evidence_01_20.json").read_text(encoding="utf-8"))
    problems = check(data)
    for problem in problems:
        print("FAIL:", problem, file=sys.stderr)
    if problems:
        return 1
    print("PASS: verified Vietnamese image coverage is independently consistent")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
