#!/usr/bin/env python3
"""Fail-closed source metadata gate; does not fetch any chapters."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BOOK = "the-demon-king-overrun"
FORBIDDEN_KEYS = {"full_text", "chapter_text", "translation_text", "raw_html", "panels"}

def valid_url(value):
    if not isinstance(value, str):
        return False
    p = urlparse(value)
    return p.scheme == "https" and bool(p.hostname)

def validate(queue, registry, canon):
    problems = []
    def need(ok, reason):
        if not ok:
            problems.append(reason)
    need(queue.get("book_id") == BOOK == registry.get("book_id"), "book ID mismatch")
    need(queue.get("source_import") == "user_supplied_text_only", "source import must remain user-supplied")
    need(queue.get("public_chapter_publication", "").startswith("blocked"), "public publication must remain blocked")
    need(queue.get("defer_chapters_before") == 137, "prior chapters must be deferred")
    arc = queue.get("priority_arc", {})
    need(arc.get("first_novel_chapter") == 137, "priority must start at novel chapter 137")
    need(arc.get("end_novel_chapter") is None or arc.get("end_confidence") == "verified", "do not assert unverified arc end")
    if arc.get("completion_candidate_novel_chapter") is not None:
        need(arc["completion_candidate_novel_chapter"] >= 137, "completion candidate before priority arc")
        need(arc.get("completion_candidate_confidence") != "verified", "completion not yet scene-verified")
    if arc.get("confirmed_mobile_by_novel_chapter") is not None:
        need(arc["confirmed_mobile_by_novel_chapter"] >= 137, "retrospective anchor before priority arc")
    beats = arc.get("story_beats", [])
    need(isinstance(beats, list) and bool(beats), "story beats missing")
    for i, beat in enumerate(beats):
        chapter = beat.get("chapter")
        need(type(chapter) is int and chapter >= 137, f"story_beats[{i}]: invalid novel chapter")
        need(valid_url(beat.get("source_url")), f"story_beats[{i}]: HTTPS provenance required")
        need(not any(key in beat for key in FORBIDDEN_KEYS), f"story_beats[{i}]: chapter text must not be stored")
        need(beat.get("status") not in {"published", "translated"}, f"story_beats[{i}]: metadata must not claim publication")
    release = registry.get("public_release", {})
    need(release.get("rights_status") == "pending", "unlicensed work rights cannot be cleared")
    for flag in ("translation_rights_verified", "online_distribution_rights_verified", "allowed_to_publish"):
        need(release.get(flag) is False, f"public_release.{flag} must be false")
    need(not release.get("permission_document"), "cannot invent rights evidence")
    personal = registry.get("personal_reading", {})
    need(personal.get("source_origin") == "user_supplied_local_text_only", "personal intake cannot scrape websites")
    for flag in ("upload_to_github", "auto_scrape", "auto_publish"):
        need(personal.get(flag) is False, f"personal_reading.{flag} must be false")
    need(personal.get("remote_ai_requires_explicit_opt_in") is True, "remote model needs opt-in")
    for i, source in enumerate(registry.get("sources", [])):
        need(valid_url(source.get("url")), f"sources[{i}]: HTTPS URL required")
        for flag in ("may_fetch_full_chapters", "may_translate_or_republish"):
            need(source.get(flag) is False, f"sources[{i}]: cannot authorize full-text use")
        need(not source.get("license_evidence"), f"sources[{i}]: unverified license")
    works = [w for w in canon.get("works", []) if w.get("book_id") == BOOK]
    need(len(works) == 1, "canonical work missing or duplicated")
    if len(works) == 1:
        w = works[0]
        need(w.get("rights_status") == "pending", "canonical rights status changed without review")
        need(w.get("allowed_to_publish") is False, "canonical public publication must remain false")
        need(w.get("allowed_to_translate") is False, "canonical translation pipeline remains disabled")
    return problems

def main():
    try:
        queue = json.loads((ROOT / "translation/reading_queue.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation/source_registry.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "translation/canon.json").read_text(encoding="utf-8"))
        errors = validate(queue, registry, canon)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL: source metadata: {exc}", file=sys.stderr)
        return 1
    if errors:
        for item in errors:
            print("FAIL: " + item, file=sys.stderr)
        return 1
    print(f"PASS: source rights pending; {len(queue['priority_arc']['story_beats'])} indexed beats; no third-party chapter import")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
