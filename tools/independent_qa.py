#!/usr/bin/env python3
"""Offline independent QA of user-supplied source and private draft; never approves."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = Path.home() / ".local/share/visunovel-private"
MANUAL = ("meaning", "Vietnamese_fluency", "POV", "names_and_identity",
          "speaker_attribution", "relationship_phase", "scene_continuity")
MARKERS = ("[CẦN_XƯNG_HÔ]", "[CHƯA_RÕ]", "[TODO]", "[TBD]", "[DEFER]")
NUMBERS = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")
HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
QUOTES = re.compile(r'“([^”]+)”|"([^"]+)"')

def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def paragraphs(s):
    return [x.strip() for x in re.split(r"\n\s*\n", s.replace("\r\n", "\n")) if x.strip()]

def speech(s):
    matches = QUOTES.findall(s)
    if matches:
        return " ".join(a or b for a, b in matches)
    return s if s.lstrip().startswith(("—", "–")) else ""

def contains(s, word):
    return bool(word and re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", s, re.I))

def inspect(source, draft, canon, book_id, chapter, annotations=None, expected_hash=None):
    """Report only codes, indices, counts and hashes: never source/draft excerpts."""
    issues = []
    def flag(code, paragraph=None, severity="blocker"):
        x = {"code": code, "severity": severity}
        if paragraph is not None:
            x["paragraph"] = paragraph
        issues.append(x)
    works = {w.get("book_id"): w for w in canon.get("works", [])}
    work = works.get(book_id, {})
    if not work:
        flag("UNKNOWN_WORK")
    if not isinstance(chapter, int) or chapter < 1:
        flag("INVALID_CHAPTER")
    s, d = paragraphs(source), paragraphs(draft)
    if not s or not d:
        flag("EMPTY_TEXT")
    if len(s) != len(d):
        flag("PARAGRAPH_COUNT_MISMATCH")
    if expected_hash and digest(source) != expected_hash:
        flag("SOURCE_HASH_MISMATCH")
    if source and draft and not .25 <= len(draft) / len(source) <= 4:
        flag("SUSPICIOUS_LENGTH_RATIO", severity="warning")
    for i, (a, b) in enumerate(zip(s, d)):
        if NUMBERS.findall(a) != NUMBERS.findall(b):
            flag("NUMBERS_CHANGED", i)
        if any(t.casefold() in b.casefold() for t in MARKERS):
            flag("UNRESOLVED_MARKER", i)
        if HANGUL.search(b):
            flag("UNTRANSLATED_HANGUL", i, "warning")
        if i and b.strip() == d[i-1].strip() and a.strip() != s[i-1].strip():
            flag("SUSPECT_DUPLICATE_PARAGRAPH", i)
    for i in range(len(s), len(d)):
        if any(t.casefold() in d[i].casefold() for t in MARKERS):
            flag("UNRESOLVED_MARKER", i)
    for term in canon.get("terms", []):
        if term.get("book_id") != book_id or not term.get("locked"):
            continue
        names = [term.get("source", "")] + term.get("aliases", [])
        if term.get("target") and any(n and n.casefold() in source.casefold() for n in names):
            if term["target"].casefold() not in draft.casefold():
                flag("LOCKED_TERM_MISSING")
    rows = []
    if annotations is not None:
        if not isinstance(annotations, dict) or annotations.get("book_id") != book_id or annotations.get("chapter") != chapter:
            flag("ANNOTATION_WORK_CHAPTER_MISMATCH")
        elif not isinstance(annotations.get("dialogues"), list):
            flag("ANNOTATION_FORMAT_INVALID")
        else:
            rows = annotations["dialogues"]
    people = {p.get("id") for p in canon.get("characters", []) if p.get("book_id") == book_id}
    edges = [r for r in canon.get("relationships", []) if r.get("book_id") == book_id and r.get("locked")]
    seen = set()
    observations = {}
    for row in rows:
        if not isinstance(row, dict):
            flag("ANNOTATION_NOT_OBJECT")
            continue
        ix = row.get("paragraph")
        if type(ix) is not int or not 0 <= ix < len(d) or ix in seen:
            flag("ANNOTATION_INDEX_INVALID")
            continue
        seen.add(ix)
        a, b, phase = row.get("speaker"), row.get("addressee"), row.get("phase")
        if a not in people or b not in people or a == b:
            flag("UNKNOWN_SPEAKER_OR_ADDRESSEE", ix)
            continue
        if row.get("review_status") != "approved" or not row.get("evidence"):
            flag("DIALOGUE_REVIEW_MISSING", ix)
        matches = [e for e in edges if e.get("speaker") == a and e.get("addressee") == b
                   and e.get("phase") == phase and e.get("reviewed_by") and e.get("evidence")
                   and type(e.get("valid_from_chapter")) is int
                   and e["valid_from_chapter"] <= chapter
                   and (e.get("valid_to_chapter") is None or chapter <= e["valid_to_chapter"])
                   and (not e.get("scene_scope") or e["scene_scope"] == row.get("scene", annotations.get("scene")))]
        if len(matches) != 1:
            flag("DIRECTED_RELATION_UNVERIFIED", ix)
        else:
            if any(row.get(k) != matches[0].get(k) for k in ("self_pronoun", "address_pronoun")):
                flag("PRONOUN_DRIFT", ix)
        utterance = speech(d[ix])
        if not utterance:
            flag("NO_ISOLATED_SPEECH", ix)
        elif any(not contains(utterance, row.get(k)) for k in ("self_pronoun", "address_pronoun")):
            flag("PRONOUN_ABSENT_FROM_SPEECH", ix)
        observations.setdefault((a, b), []).append((ix, phase))
    for ix, para in enumerate(d):
        if (para.lstrip().startswith(("“", '"', "—", "–")) or QUOTES.search(para)) and ix not in seen:
            flag("DIALOGUE_ANNOTATION_MISSING", ix)
    for (a, b), events in observations.items():
        events.sort()
        for (i, old), (j, new) in zip(events, events[1:]):
            if old == new:
                continue
            matches = [t for t in canon.get("relationship_transitions", [])
                       if t.get("book_id") == book_id and t.get("speaker") == a and t.get("addressee") == b
                       and t.get("from_phase") == old and t.get("to_phase") == new
                       and t.get("chapter") == chapter and i < t.get("paragraph", -1) <= j
                       and all(t.get(k) for k in ("review_id", "reviewed_by", "evidence", "trigger"))]
            if len(matches) != 1:
                flag("PHASE_TRANSITION_UNREVIEWED", j)
    blockers = sum(x["severity"] == "blocker" for x in issues)
    return {"schema_version": 1, "book_id": book_id, "chapter": chapter,
            "source_sha256": digest(source), "draft_sha256": digest(draft),
            "source_paragraphs": len(s), "draft_paragraphs": len(d),
            "rights_status": work.get("rights_status", "unknown"),
            "qa_status": "blocked" if blockers else "needs_review",
            "manual_review_required": True,
            "manual_checks": {k: "pending" for k in MANUAL},
            "publishable": False, "public_release_authorized": False,
            "findings": issues, "blockers": blockers}

def read_text(path, allowed):
    if path.suffix.lower() not in allowed or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("Missing/invalid/oversized input")
    return path.read_text(encoding="utf-8-sig")

def save_private(report, path, root=PRIVATE):
    home = root.expanduser().resolve()
    dest = path.expanduser().resolve()
    if home.is_relative_to(ROOT.resolve()) or dest == home or not dest.is_relative_to(home):
        raise ValueError("Report path must be in private home outside repo")
    dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = dest.with_name(dest.name + ".tmp")
    try:
        tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("draft", type=Path)
    p.add_argument("--book-id", default="the-demon-king-overrun")
    p.add_argument("--chapter", type=int, default=137)
    p.add_argument("--annotations", type=Path)
    p.add_argument("--expected-source-sha256")
    p.add_argument("--report", type=Path)
    args = p.parse_args(argv)
    try:
        source = read_text(args.source, (".txt", ".md"))
        draft = read_text(args.draft, (".txt", ".md"))
        canon = json.loads((ROOT / "translation/canon.json").read_text(encoding="utf-8"))
        annotations = json.loads(read_text(args.annotations, (".json",))) if args.annotations else None
        if args.expected_source_sha256 and not re.fullmatch(r"[a-fA-F0-9]{64}", args.expected_source_sha256):
            raise ValueError("Invalid source SHA256")
        report = inspect(source, draft, canon, args.book_id, args.chapter, annotations, args.expected_source_sha256)
        output = args.report or PRIVATE / "reports" / (args.book_id + "-chapter-" + str(args.chapter) + ".independent-qa.json")
        save_private(report, output)
        print("QA:", report["qa_status"], "| blockers:", report["blockers"], "| private report:", output)
        print("Semantic review and publication approval are NEVER automatic.")
        return 1 if report["blockers"] else 0
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        print("QA ERROR:", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
