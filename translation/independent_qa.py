#!/usr/bin/env python3
"""Local structural QA for user-provided draft text. No network or publishing."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def clean(s: str) -> str:
    return s.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")

def digest(s: str) -> str:
    return hashlib.sha256(clean(s).encode("utf-8")).hexdigest()

def paras(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n[ \t]*\n+", clean(s)) if p.strip()]

def within(path: Path) -> bool:
    return path.expanduser().resolve().is_relative_to(ROOT.resolve())

def audit(source: str, draft: str, book_id: str, chapter: int, canon: dict, manifest: dict | None = None) -> dict:
    errors, warnings = [], []
    works = [w for w in canon.get("works", []) if w.get("book_id") == book_id]
    if len(works) != 1:
        errors.append("unknown_or_duplicate_work")
    elif works[0].get("rights_status") != "cleared" or works[0].get("allowed_to_publish") is not True:
        errors.append("public_rights_pending")
    a, b = paras(source), paras(draft)
    if not a or not b:
        errors.append("empty_source_or_draft")
    if len(a) != len(b):
        errors.append("paragraph_count_mismatch")
    if "[CẦN_XƯNG_HÔ]" in draft:
        errors.append("unresolved_address")
    if re.search(r"[\uac00-\ud7a3]", draft):
        warnings.append("possible_untranslated_korean")
    for i in range(1, len(b)):
        if len(b[i]) >= 35 and b[i].casefold() == b[i-1].casefold() and (i >= len(a) or a[i] != a[i-1]):
            warnings.append("repeated_draft_paragraph")
    if manifest is None:
        warnings.append("missing_translation_manifest")
    else:
        if manifest.get("source_sha256") != digest(source):
            errors.append("source_checksum_mismatch")
        if manifest.get("book_id") != book_id or type(manifest.get("chapter")) is not int or manifest["chapter"] != chapter:
            errors.append("manifest_identity_mismatch")
        if manifest.get("qa_status") in {"passed", "approved", "published", "ready"}:
            errors.append("unreviewed_approval_claim")
        if manifest.get("public_release_authorized") is True or manifest.get("draft_only") is False:
            errors.append("unsafe_publication_flag")
    for term in canon.get("terms", []):
        if term.get("book_id") != book_id or term.get("locked") is not True:
            continue
        src, dst = term.get("source"), term.get("target")
        if isinstance(src, str) and isinstance(dst, str) and src and dst and src.casefold() in source.casefold() and dst.casefold() not in draft.casefold():
            warnings.append("glossary_term_needs_review")
    return {
        "book_id": book_id, "chapter": chapter, "source_sha256": digest(source),
        "draft_sha256": digest(draft), "source_paragraphs": len(a), "draft_paragraphs": len(b),
        "blockers": sorted(set(errors)), "warnings": sorted(set(warnings)),
        "literary_qa": "NOT_REVIEWED", "public_release": "BLOCKED",
        "note": "Structural checks only; human source, speaker, honorific and rights review still required."
    }

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("draft", type=Path)
    p.add_argument("--book-id", default="the-demon-king-overrun")
    p.add_argument("--chapter", type=int, default=137)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        if not args.source.is_file() or not args.draft.is_file():
            raise ValueError("Missing local source or draft file")
        if args.source.suffix.lower() not in {".txt", ".md"} or args.draft.suffix.lower() not in {".txt", ".md"}:
            raise ValueError("Only TXT/MD inputs supported")
        if args.source.stat().st_size > 1048576 or args.draft.stat().st_size > 1048576:
            raise ValueError("1 MB limit")
        canon = json.loads((ROOT / "translation/canon.json").read_text(encoding="utf-8"))
        work = next((w for w in canon.get("works", []) if w.get("book_id") == args.book_id), None)
        if work is None:
            raise ValueError("Unknown work")
        if work.get("rights_status") != "cleared" and (within(args.source) or within(args.draft)):
            raise ValueError("Private source/draft must be outside repository")
        out = args.report or args.draft.with_name(args.draft.stem + ".qa.json")
        if within(out):
            raise ValueError("QA report must be outside repository")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
        report = audit(args.source.read_text(encoding="utf-8-sig"),
                       args.draft.read_text(encoding="utf-8-sig"),
                       args.book_id, args.chapter, canon, manifest)
        out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with out.open("x", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
        out.chmod(0o600)
        print("Local QA report:", out, "blockers:", len(report["blockers"]))
        print("Literary QA remains NOT_REVIEWED; public release remains BLOCKED.")
        return 1 if report["blockers"] else 0
    except (OSError, ValueError, UnicodeError) as exc:
        print("QA ERROR:", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
