"""Private draft helpers: fingerprint, directed context, QA and safe output."""
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home() / ".local/share/visunovel-private"

def digest(obj):
    if not isinstance(obj, str):
        obj = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(obj.encode("utf-8")).hexdigest()

def private_path(path, root=HOME, repo=REPO):
    root = Path(root).expanduser().resolve()
    dest = Path(path).expanduser().resolve()
    if root.is_relative_to(Path(repo).resolve()) or dest == root or not dest.is_relative_to(root):
        raise ValueError("Private output must be outside Git and inside private home")
    return dest

def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

def chapter_context(canon, book_id, chapter, source, annotations=None):
    if not any(w.get("book_id") == book_id for w in canon["works"]):
        raise ValueError("Unknown book_id")
    annotations = annotations or []
    chars = [c for c in canon.get("characters", []) if c.get("book_id") == book_id and c.get("locked")]
    ids = {c["id"] for c in chars}
    selected = set()
    for c in chars:
        if any(name and name.casefold() in source.casefold() for name in
               [c.get("canonical_name", "")] + c.get("aliases", [])):
            selected.add(c["id"])
    edges = [r for r in canon.get("relationships", []) if r.get("book_id") == book_id
             and r.get("locked") and r.get("reviewed_by") and r.get("evidence")
             and r.get("valid_from_chapter", 1) <= chapter
             and (r.get("valid_to_chapter") is None or chapter <= r["valid_to_chapter"])]
    issues = []
    seen = set()
    for entry in annotations:
        ix = entry.get("paragraph")
        if not isinstance(ix, int) or ix < 0 or ix >= len(paragraphs(source)) or ix in seen:
            issues.append("invalid/duplicate paragraph index")
            continue
        seen.add(ix)
        a, b, phase = entry.get("speaker"), entry.get("addressee"), entry.get("phase")
        if a not in ids or b not in ids:
            issues.append(f"paragraph {ix}: unknown speaker/addressee; defer")
            continue
        selected.update((a, b))
        matches = [r for r in edges if r.get("speaker") == a and r.get("addressee") == b and r.get("phase") == phase]
        if len(matches) != 1:
            issues.append(f"paragraph {ix}: unverified relation {a}->{b}/{phase}; defer")
    terms = []
    for t in canon.get("terms", []):
        if t.get("book_id") == book_id and t.get("locked"):
            if any(alias and alias.casefold() in source.casefold() for alias in
                   [t.get("source", "")] + t.get("aliases", [])):
                terms.append(t)
    return {"characters": [c for c in chars if c["id"] in selected],
            "directed_relations": [r for r in edges if r.get("speaker") in selected or r.get("addressee") in selected],
            "locked_terms": terms, "unreviewed_annotations": annotations}, issues

def qa_paragraphs(source, translated, terms=()):
    problems = []
    if len(paragraphs(source)) != len(paragraphs(translated)):
        problems.append("PARAGRAPH_COUNT")
    if "[CẦN_XƯNG_HÔ]" in translated:
        problems.append("PRONOUN_UNRESOLVED")
    for term in terms:
        if term.get("target") and term.get("source", "").casefold() in source.casefold():
            if term["target"].casefold() not in translated.casefold():
                problems.append("LOCKED_TERM_MISSING")
    return problems

def resume_guard(checkpoint, source, canon, context, model, chunk_chars):
    expected = digest({"source": digest(source), "canon": canon,
                       "context": context, "model": model, "chunk_chars": chunk_chars})
    if checkpoint is not None and checkpoint.get("job_sha256") != expected:
        raise ValueError("Checkpoint context/source/model changed; refusing resume")
    return expected
