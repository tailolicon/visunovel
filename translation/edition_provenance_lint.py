#!/usr/bin/env python3
"""Guard comic edition identity; source mirrors are never the selected baseline by default.

This audits declared metadata only. It does not inspect images or certify reviews.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
KINDS = {"manhwa_vi_panel", "manhwa_english_chapter_title", "novel_english_secondary"}

def host(value: object) -> str:
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        return ""
    return (parsed.hostname or "").lower().rstrip(".")

def same_or_subdomain(child: str, parent: str) -> bool:
    return bool(parent and (child == parent or child.endswith("." + parent)))

def check(data: dict) -> list[str]:
    errors: list[str] = []
    baseline_host = host(data.get("requested_source"))
    if not baseline_host:
        errors.append("requested source is not a valid HTTPS URL")
    sources: dict[str, dict] = {}
    for i, source in enumerate(data.get("sources", [])):
        sid = source.get("id")
        if not isinstance(sid, str) or not sid or sid in sources:
            errors.append(f"source[{i}]: missing/duplicate edition ID")
            continue
        if source.get("medium") not in KINDS:
            errors.append(f"source[{i}]: missing/invalid edition medium")
        if not host(source.get("url")):
            errors.append(f"source[{i}]: invalid source URL")
        if source.get("selected_baseline") is not False and source.get("selected_baseline") is not True:
            errors.append(f"source[{i}]: selected_baseline must be explicit boolean")
        if source.get("selected_baseline") and host(source.get("url")) != baseline_host:
            errors.append(f"source[{i}]: mirror cannot impersonate selected baseline")
        sources[sid] = source
    if not sources:
        errors.append("no edition source registry")
    for i, observation in enumerate(data.get("observations", [])):
        loc = f"observation[{i}]"
        sid = observation.get("source_edition_id")
        source = sources.get(sid)
        if source is None:
            errors.append(loc + ": missing/unknown edition ID")
            continue
        if source.get("medium") != observation.get("medium"):
            errors.append(loc + ": edition medium mismatch")
        evidence_host = host(observation.get("source_url"))
        source_host = host(source.get("url"))
        if not same_or_subdomain(evidence_host, source_host):
            errors.append(loc + ": image/chapter URL host not attributable to registered edition")
        primary = observation.get("selected_baseline_verified")
        if type(primary) is not bool:
            errors.append(loc + ": selected_baseline_verified must be explicit boolean")
        if observation.get("medium") == "manhwa_vi_panel":
            panel = observation.get("panel_number")
            if type(panel) is not int or panel <= 0:
                errors.append(loc + ": panel evidence requires positive panel_number")
            if observation.get("edition_match_status") not in ("unverified", "confirmed"):
                errors.append(loc + ": invalid Vietnamese edition match status")
            if not observation.get("speaker_identity_status") or not observation.get("addressee_identity_status"):
                errors.append(loc + ": speaker/addressee identity resolution must be explicit")
            if primary:
                if not source.get("selected_baseline") or evidence_host != baseline_host:
                    errors.append(loc + ": mirror cannot certify selected-source Vietnamese dialogue")
                if observation.get("edition_match_status") != "confirmed":
                    errors.append(loc + ": selected-source claim lacks confirmed edition match")
                if not observation.get("visual_review_id") or not observation.get("visual_reviewed_by"):
                    errors.append(loc + ": selected-source claim needs independent visual review")
        elif primary:
            errors.append(loc + ": non-Vietnamese-panel cannot certify selected baseline")
        elif observation.get("edition_match_status") != "not_applicable":
            errors.append(loc + ": secondary metadata cannot claim Vietnamese edition match")
    return errors

def main() -> int:
    try:
        data = json.loads((ROOT / "translation/evidence_01_20.json").read_text(encoding="utf-8"))
        errors = check(data)
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL: invalid edition metadata: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    selected = sum(bool(o.get("selected_baseline_verified")) for o in data["observations"])
    mirror = sum(o.get("medium") == "manhwa_vi_panel" and not o.get("selected_baseline_verified") for o in data["observations"])
    print(f"PASS: {selected} selected-baseline panels; {mirror} unmatched Vietnamese mirror panels; all editions explicitly labeled")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
