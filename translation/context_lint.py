#!/usr/bin/env python3
"""Fail-closed editorial checks for character identity, directed address and lore.

This is a complementary context QA gate, not a semantic source comparison.
No network requests, AI inference, or automatic promotion of glossary candidates.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).casefold().split())


def spoken_segments(paragraph: str) -> str:
    """Exclude narration outside quote marks from pronoun evidence."""
    curly = re.findall(r"“([^”]*)”", paragraph)
    straight = re.findall(r'"([^"]*)"', paragraph)
    if curly or straight:
        return " ".join(curly + straight)
    if paragraph.lstrip().startswith(("—", "–", "-")):
        return paragraph
    return ""


def contains_word(text: str, word: str) -> bool:
    return bool(word and re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text, re.IGNORECASE))


def validate(canon: dict, chapters: list[dict], world_bible: dict | None = None) -> list[str]:
    errors: list[str] = []

    def err(path: str, message: str) -> None:
        errors.append(f"{path}: {message}")

    works: dict[str, dict] = {}
    for idx, work in enumerate(canon.get("works", [])):
        book_id = work.get("book_id")
        if not isinstance(book_id, str) or not book_id:
            err(f"works[{idx}]", "missing book_id")
        elif book_id in works:
            err(f"works[{idx}]", f"duplicate book_id {book_id}")
        else:
            works[book_id] = work

    people: dict[str, dict] = {}
    alias_owners: dict[tuple[str, str], str] = {}
    for idx, person in enumerate(canon.get("characters", [])):
        loc = f"characters[{idx}]"
        cid, book = person.get("id"), person.get("book_id")
        if not cid or not isinstance(cid, str):
            err(loc, "missing stable character id")
            continue
        if cid in people:
            err(loc, f"duplicate character id {cid}")
        else:
            people[cid] = person
        if book not in works:
            err(loc, f"unknown book_id {book}")
        names = [person.get("canonical_name")] + person.get("aliases", [])
        if not names[0]:
            err(loc, "missing canonical_name")
        for name in names:
            norm = normalized(name)
            if not norm:
                err(loc, "empty name/alias")
                continue
            key = (book, norm)
            other = alias_owners.get(key)
            if other and other != cid:
                err(loc, f"identity alias collision {name!r}: {other} vs {cid}")
            alias_owners[key] = cid

    edges: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    edge_ids: set[str] = set()
    pair_edges: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for idx, edge in enumerate(canon.get("relationships", [])):
        loc = f"relationships[{idx}]"
        eid, book = edge.get("id"), edge.get("book_id")
        speaker, addressee, phase = edge.get("speaker"), edge.get("addressee"), edge.get("phase")
        if not eid or eid in edge_ids:
            err(loc, f"missing/duplicate relationship id {eid!r}")
        else:
            edge_ids.add(eid)
        if speaker == addressee:
            err(loc, "self-address needs an explicit separate model; directed pair is reflexive")
        for field, cid in (("speaker", speaker), ("addressee", addressee)):
            if cid not in people or people[cid].get("book_id") != book:
                err(loc, f"{field} {cid!r} is not a character of {book!r}")
        if not isinstance(phase, str) or not phase:
            err(loc, "missing relationship phase")
        start, end = edge.get("valid_from_chapter"), edge.get("valid_to_chapter")
        if not isinstance(start, int) or isinstance(start, bool) or start < 1:
            err(loc, "valid_from_chapter must be a positive integer")
        if end is not None and (not isinstance(end, int) or isinstance(end, bool) or not isinstance(start, int) or end < start):
            err(loc, "invalid valid_to_chapter")
        for pronoun in ("self_pronoun", "address_pronoun"):
            if not edge.get(pronoun):
                err(loc, f"missing {pronoun}")
        if edge.get("locked") and (not edge.get("evidence") or not edge.get("reviewed_by")):
            err(loc, "locked relation needs evidence and reviewed_by")
        if not edge.get("locked"):
            err(loc, "unlocked relation cannot authorize publication")
        key = (book, speaker, addressee, phase)
        edges[key].append(edge)
        pair_edges[(book, speaker, addressee)].append(edge)

    def overlap(a: dict, b: dict) -> bool:
        a1, b1 = a.get("valid_from_chapter"), b.get("valid_from_chapter")
        if not isinstance(a1, int) or not isinstance(b1, int):
            return False
        a2, b2 = a.get("valid_to_chapter"), b.get("valid_to_chapter")
        return a1 <= (b2 if isinstance(b2, int) else float("inf")) and b1 <= (a2 if isinstance(a2, int) else float("inf"))

    for pair, variants in pair_edges.items():
        for i, a in enumerate(variants):
            for b in variants[i + 1:]:
                if not overlap(a, b):
                    continue
                if a.get("phase") == b.get("phase"):
                    err("relationships", f"ambiguous overlapping locked edges for {pair} phase {a.get('phase')}")
                elif not (a.get("scene_scope") and b.get("scene_scope") and a["scene_scope"] != b["scene_scope"]):
                    err("relationships", f"overlapping phases for {pair} require distinct explicit scene_scope")

    transitions: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for idx, transition in enumerate(canon.get("relationship_transitions", [])):
        loc = f"relationship_transitions[{idx}]"
        book, speaker, addressee = (transition.get(k) for k in ("book_id", "speaker", "addressee"))
        old, new = transition.get("from_phase"), transition.get("to_phase")
        chapter, paragraph = transition.get("chapter"), transition.get("paragraph", 0)
        if old == new or not old or not new:
            err(loc, "transition must change between two named phases")
        if not isinstance(chapter, int) or isinstance(chapter, bool) or chapter < 1:
            err(loc, "chapter must be a positive integer")
        if not isinstance(paragraph, int) or isinstance(paragraph, bool) or paragraph < 0:
            err(loc, "paragraph must be a nonnegative integer")
        if not transition.get("reviewed_by") or not transition.get("review_id") or not transition.get("evidence") or not transition.get("trigger"):
            err(loc, "transition needs reviewer, review_id, evidence and narrative trigger")
        if (book, speaker, addressee, old) not in edges or (book, speaker, addressee, new) not in edges:
            err(loc, "transition must refer to both registered directed phases")
        transitions[(book, speaker, addressee, old, new)].append(transition)

    term_owners: dict[tuple[str, str], str] = {}
    for idx, term in enumerate(canon.get("terms", [])):
        if not term.get("locked"):
            continue
        for alias in [term.get("source")] + term.get("aliases", []):
            key = (term.get("book_id", "*"), normalized(alias))
            if not key[1]:
                err(f"terms[{idx}]", "locked term has an empty source/alias")
            other = term_owners.get(key)
            if other and other != term.get("id"):
                err(f"terms[{idx}]", f"locked terminology collision {alias!r}")
            term_owners[key] = term.get("id")
    for queue_name in ("term_review_queue", "relationship_review_queue"):
        for idx, candidate in enumerate(canon.get(queue_name, [])):
            if candidate.get("locked") or candidate.get("review_status") == "approved":
                err(f"{queue_name}[{idx}]", "review queue item cannot be auto-promoted")

    lore: dict[str, dict] = {}
    if world_bible is not None:
        for idx, fact in enumerate(world_bible.get("facts", [])):
            loc, fid, book = f"world_bible.facts[{idx}]", fact.get("id"), fact.get("book_id")
            if not fid or fid in lore:
                err(loc, f"missing/duplicate fact id {fid!r}")
            else:
                lore[fid] = fact
            if book not in works:
                err(loc, f"unknown work {book!r}")
            if fact.get("status") not in ("confirmed", "candidate", "unknown"):
                err(loc, "invalid fact status")
            if fact.get("status") == "confirmed":
                if not fact.get("statement") or not fact.get("source_reference") or not fact.get("reviewed_by"):
                    err(loc, "confirmed fact requires statement, source_reference and reviewer")
            if fact.get("status") != "confirmed" and fact.get("locked"):
                err(loc, "unknown/candidate lore cannot be locked")
            if fact.get("kind") == "character_knowledge":
                who = fact.get("character_id")
                if who not in people or people[who].get("book_id") != book:
                    err(loc, f"unknown knowledge holder {who!r}")
                start = fact.get("known_from_chapter")
                if not isinstance(start, int) or isinstance(start, bool) or start < 1:
                    err(loc, "knowledge must have positive known_from_chapter")

    observations: dict[tuple[str, str, str], list[tuple[int, int, str, str]]] = defaultdict(list)
    seen_chapters: set[tuple[str, int]] = set()
    for ci, chapter in enumerate(chapters):
        book, number = chapter.get("bookId"), chapter.get("chapter")
        loc = f"chapters[{ci}]({book}/{number})"
        if book not in works:
            err(loc, "unknown book")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            err(loc, "invalid chapter number")
            continue
        if (book, number) in seen_chapters:
            err(loc, "duplicate chapter number")
        seen_chapters.add((book, number))
        paragraphs = chapter.get("paragraphs", [])
        if not isinstance(paragraphs, list):
            err(loc, "paragraphs must be an array")
            continue
        used: set[int] = set()
        for di, d in enumerate(chapter.get("dialogues", [])):
            dloc = f"{loc}.dialogues[{di}]"
            index = d.get("paragraph")
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(paragraphs) or index in used:
                err(dloc, "invalid or repeated paragraph index")
                continue
            used.add(index)
            speaker, addressee, phase = d.get("speaker"), d.get("addressee"), d.get("phase")
            for field, cid in (("speaker", speaker), ("addressee", addressee)):
                if cid not in people or people[cid].get("book_id") != book:
                    err(dloc, f"unknown {field} {cid!r}")
            matches = [edge for edge in edges.get((book, speaker, addressee, phase), [])
                       if isinstance(edge.get("valid_from_chapter"), int)
                       and edge["valid_from_chapter"] <= number
                       and (edge.get("valid_to_chapter") is None or number <= edge["valid_to_chapter"])
                       and (not edge.get("scene_scope") or edge["scene_scope"] == d.get("scene", chapter.get("scene")))]
            if len(matches) != 1:
                err(dloc, f"no unique directed relation {speaker}->{addressee}/{phase} at chapter {number}")
            else:
                edge = matches[0]
                for key in ("self_pronoun", "address_pronoun"):
                    if d.get(key) != edge.get(key):
                        err(dloc, f"PRONOUN DRIFT {key}: {d.get(key)!r} != {edge.get(key)!r}")
            if d.get("review_status") != "approved" or not d.get("evidence"):
                err(dloc, "dialogue not reviewed with evidence")
            speech = spoken_segments(paragraphs[index]) if isinstance(paragraphs[index], str) else ""
            if not speech:
                err(dloc, "cannot isolate quoted speech from narration")
            else:
                for key in ("self_pronoun", "address_pronoun"):
                    if not contains_word(speech, d.get(key, "")):
                        err(dloc, f"{key} lacks evidence inside spoken quote")
            for fact_id in d.get("knowledge_refs", []):
                fact = lore.get(fact_id)
                if fact is None or fact.get("book_id") != book:
                    err(dloc, f"unknown world fact reference {fact_id!r}")
                elif fact.get("kind") == "character_knowledge" and (fact.get("character_id") != speaker or number < fact.get("known_from_chapter", 10**9)):
                    err(dloc, f"spoiler/knowledge timeline violation {fact_id!r}")
            observations[(book, speaker, addressee)].append((number, index, phase, d.get("scene", chapter.get("scene", ""))))
        for ix, para in enumerate(paragraphs):
            if isinstance(para, str) and para.lstrip().startswith(("“", '"', "—")) and ix not in used:
                err(loc, f"direct speech paragraph {ix} missing annotation")

    for pair, obs in observations.items():
        obs.sort(key=lambda row: (row[0], row[1]))
        for prev, curr in zip(obs, obs[1:]):
            if prev[2] == curr[2]:
                continue
            options = transitions.get((*pair, prev[2], curr[2]), [])
            matching = [t for t in options
                        if (prev[0], prev[1]) < (t.get("chapter", -1), t.get("paragraph", -1)) <= (curr[0], curr[1])
                        and (not t.get("scene") or t["scene"] == curr[3])
                        and t.get("review_id") and t.get("reviewed_by") and t.get("evidence") and t.get("trigger")]
            if len(matching) != 1:
                err("continuity", f"unapproved phase change {pair}: {prev[2]}@{prev[:2]} -> {curr[2]}@{curr[:2]}")

    return errors


def main() -> int:
    def read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        canon = read(ROOT / "translation/canon.json")
        library = read(ROOT / "data/library.json")
        world_bible_path = ROOT / "translation/world_bible.json"
        world_bible = read(world_bible_path) if world_bible_path.exists() else None
        chapters = []
        for book in library["books"]:
            for item in book.get("chapters", []):
                rel = Path(item["path"])
                if rel.is_absolute() or ".." in rel.parts:
                    raise ValueError(f"Unsafe chapter path {rel}")
                chapters.append(read(ROOT / rel))
        issues = validate(canon, chapters, world_bible)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: context input invalid: {exc}", file=sys.stderr)
        return 1
    if issues:
        print("FAIL: context integrity", file=sys.stderr)
        for issue in issues:
            print(" - " + issue, file=sys.stderr)
        return 1
    print(f"PASS: {len(canon.get('characters', []))} characters, {len(canon.get('relationships', []))} directed relations, {len(chapters)} published demo chapters, {len((world_bible or {}).get('facts', []))} lore facts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
