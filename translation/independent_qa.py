#!/usr/bin/env python3
"""Offline, private-only structural and directed-address QA for user-supplied drafts.

This module NEVER approves literary quality or publication. No network calls.
Source and draft text are read from local files; reports contain only hashes,
counts and stable issue codes, never paragraphs, API keys or source quotations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_HOME = Path.home() / ".local" / "share" / "visunovel-private"
MAX_BYTES = 1024 * 1024
VALID_TEXT_EXT = {".txt", ".md"}
APPROVAL_STATES = {"approved", "passed", "published", "ready"}


def clean(text: str) -> str:
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


def digest(text: str) -> str:
    return hashlib.sha256(clean(text).encode("utf-8")).hexdigest()


def paras(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n[ \t]*\n+", clean(text)) if p.strip()]


def within(path: Path, root: Path = ROOT) -> bool:
    return path.expanduser().resolve().is_relative_to(root.expanduser().resolve())


def _approved_relation(entry: dict, canon: dict, book_id: str, chapter: int) -> bool:
    speaker, addressee, phase = (entry.get(k) for k in ("speaker", "addressee", "phase"))
    if not all(isinstance(v, str) and v for v in (speaker, addressee, phase)):
        return False
    matches = []
    for edge in canon.get("relationships", []):
        if (edge.get("book_id"), edge.get("speaker"), edge.get("addressee"), edge.get("phase")) != (
            book_id, speaker, addressee, phase
        ):
            continue
        start, end = edge.get("valid_from_chapter"), edge.get("valid_to_chapter")
        if type(start) is not int or chapter < start or (end is not None and (type(end) is not int or chapter > end)):
            continue
        if edge.get("scene_scope") and edge.get("scene_scope") != entry.get("scene"):
            continue
        if edge.get("locked") is not True or not edge.get("evidence") or not edge.get("reviewed_by"):
            continue
        matches.append(edge)
    return (len(matches) == 1 and
            matches[0].get("self_pronoun") == entry.get("self_pronoun") and
            matches[0].get("address_pronoun") == entry.get("address_pronoun"))


def _dialogue_audit(manifest: dict, canon: dict, book_id: str, chapter: int, paragraph_count: int) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    rows = manifest.get("dialogue_reviews")
    if rows is None:
        return blockers, ["directed_dialogue_review_missing"]
    if not isinstance(rows, list):
        return ["invalid_dialogue_review_schema"], warnings
    seen: set[tuple[int, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            blockers.append("invalid_dialogue_review_schema")
            continue
        index = row.get("paragraph")
        if type(index) is not int or not 0 <= index < paragraph_count:
            blockers.append("dialogue_paragraph_out_of_range")
            continue
        pair = (index, row.get("speaker"), row.get("addressee"))
        if any(not isinstance(x, str) or not x for x in pair[1:]):
            blockers.append("dialogue_identity_unresolved")
            continue
        if pair in seen:
            blockers.append("duplicate_directed_dialogue_review")
        seen.add(pair)
        status = row.get("review_status")
        if status == "pending":
            warnings.append("directed_dialogue_review_pending")
            continue
        if status != "approved":
            blockers.append("invalid_dialogue_review_status")
            continue
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in
                   ("source_scene_ref", "reviewed_by", "review_id")):
            blockers.append("approved_dialogue_lacks_scene_review")
        if not _approved_relation(row, canon, book_id, chapter):
            blockers.append("unverified_directed_pronoun_pair")
    return blockers, warnings


def audit(source: str, draft: str, book_id: str, chapter: int,
          canon: dict, manifest: dict | None = None) -> dict:
    """Return metadata-only QA; public release is ALWAYS blocked by this tool."""
    blockers: list[str] = []
    warnings: list[str] = []
    release_blockers = ["independent_literary_review_required", "publication_not_authorized_by_private_qa"]
    works = [w for w in canon.get("works", []) if w.get("book_id") == book_id]
    if len(works) != 1:
        blockers.append("unknown_or_duplicate_work")
        release_blockers.append("unknown_or_duplicate_work")
    elif works[0].get("rights_status") != "cleared" or works[0].get("allowed_to_publish") is not True:
        release_blockers.append("public_rights_pending")

    original, translated = paras(source), paras(draft)
    if not original or not translated:
        blockers.append("empty_source_or_draft")
    if len(original) != len(translated):
        blockers.append("paragraph_count_mismatch")
    if "[CẦN_XƯNG_HÔ]" in draft:
        blockers.append("unresolved_address")
    if re.search(r"[\uac00-\ud7a3]", draft):
        warnings.append("possible_untranslated_korean")
    for i in range(1, len(translated)):
        if (len(translated[i]) >= 35 and translated[i].casefold() == translated[i-1].casefold()
                and (i >= len(original) or original[i] != original[i-1])):
            warnings.append("repeated_draft_paragraph")

    if manifest is None:
        warnings.append("missing_translation_manifest")
        warnings.append("directed_dialogue_review_missing")
    elif not isinstance(manifest, dict):
        blockers.append("invalid_translation_manifest")
    else:
        if manifest.get("source_sha256") != digest(source):
            blockers.append("source_checksum_mismatch")
        if manifest.get("book_id") != book_id or type(manifest.get("chapter")) is not int or manifest["chapter"] != chapter:
            blockers.append("manifest_identity_mismatch")
        if manifest.get("draft_sha256") is not None and manifest["draft_sha256"] != digest(draft):
            blockers.append("draft_checksum_mismatch")
        if manifest.get("qa_status") in APPROVAL_STATES:
            blockers.append("unreviewed_approval_claim")
        if manifest.get("public_release_authorized") is True or manifest.get("draft_only") is False:
            blockers.append("unsafe_publication_flag")
        a, b = _dialogue_audit(manifest, canon, book_id, chapter, len(translated))
        blockers.extend(a)
        warnings.extend(b)

    for term in canon.get("terms", []):
        if term.get("book_id") != book_id or term.get("locked") is not True:
            continue
        src, dst = term.get("source"), term.get("target")
        if (isinstance(src, str) and isinstance(dst, str) and src and dst
                and src.casefold() in source.casefold() and dst.casefold() not in draft.casefold()):
            warnings.append("glossary_term_needs_review")

    return {
        "book_id": book_id, "chapter": chapter,
        "source_sha256": digest(source), "draft_sha256": digest(draft),
        "source_paragraphs": len(original), "draft_paragraphs": len(translated),
        "blockers": sorted(set(blockers)), "warnings": sorted(set(warnings)),
        "private_structural_qa": "BLOCKED" if blockers else "PASS_STRUCTURAL_ONLY",
        "literary_qa": "NOT_REVIEWED", "public_release": "BLOCKED",
        "release_blockers": sorted(set(release_blockers)),
        "note": "Metadata-only checks. Directed dialogue review cannot infer speakers; human source/scene review required."
    }


def _read_private_text(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in VALID_TEXT_EXT:
        raise ValueError("Input must be a regular local TXT/MD file, not a symlink")
    if within(path):
        raise ValueError("Source and draft must be outside the repository")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("1 MB input limit")
    return path.read_text(encoding="utf-8-sig")


def _write_private_report(path: Path, report: dict) -> None:
    if not within(path, PRIVATE_HOME) or within(path):
        raise ValueError("QA report must be inside the private data directory, never the repository")
    if PRIVATE_HOME.is_symlink():
        raise ValueError("Private data root must not be a symlink")
    PRIVATE_HOME.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(PRIVATE_HOME, 0o700)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent != PRIVATE_HOME:
        os.chmod(path.parent, 0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="User-provided source TXT/MD outside repository")
    parser.add_argument("draft", type=Path, help="Private draft TXT/MD outside repository")
    parser.add_argument("--book-id", default="the-demon-king-overrun")
    parser.add_argument("--chapter", type=int, default=137)
    parser.add_argument("--manifest", type=Path, help="Optional local JSON manifest, outside repository")
    parser.add_argument("--report", type=Path, help="Must be under ~/.local/share/visunovel-private")
    args = parser.parse_args()
    try:
        if args.chapter < 1 or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", args.book_id):
            raise ValueError("Invalid chapter/book identifier")
        source = _read_private_text(args.source)
        draft = _read_private_text(args.draft)
        manifest = None
        if args.manifest:
            if args.manifest.is_symlink() or within(args.manifest) or not args.manifest.is_file() or args.manifest.stat().st_size > 65536:
                raise ValueError("Manifest must be a regular local JSON file outside repository (64 KB max)")
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "translation/canon.json").read_text(encoding="utf-8"))
        report = audit(source, draft, args.book_id, args.chapter, canon, manifest)
        path = args.report or (PRIVATE_HOME / "qa" / f"{args.book_id}-ch{args.chapter}-{digest(source)[:12]}.json")
        _write_private_report(path, report)
        print(f"Private QA metadata: {path} | structural blockers: {len(report['blockers'])}")
        print("Literary QA NOT_REVIEWED; public release BLOCKED regardless of structural status.")
        return 1 if report["blockers"] else 0
    except (OSError, ValueError, UnicodeError, TypeError) as exc:
        print(f"QA ERROR: {type(exc).__name__} (details withheld to protect private paths/content)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
