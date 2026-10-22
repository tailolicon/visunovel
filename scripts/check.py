#!/usr/bin/env python3
"""visuNovel publication gate: fail closed on rights and directed pronoun context."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
errors = []
def load(path):
    try:
        return json.loads((ROOT/path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"{path}: cannot parse: {exc}")
        return {}
def require(test, message):
    if not test: errors.append(message)
def has_word(text, word):
    return bool(re.search(r"(?<!\w)"+re.escape(str(word))+r"(?!\w)", text, flags=re.IGNORECASE))
lib = load(Path("data/library.json"))
canon = load(Path("translation/canon.json"))
books = lib.get("books", [])
require(isinstance(books, list), "library.books must be an array")
works = {x.get("book_id"):x for x in canon.get("works", [])}
people = {x.get("id"):x for x in canon.get("characters", [])}
relations = canon.get("relationships", [])
seen = set()
for book in books:
    bid=book.get("id")
    require(bid and bid not in seen, f"Duplicate/missing book ID: {bid}")
    seen.add(bid)
    work=works.get(bid, {})
    chapters=book.get("chapters", [])
    require(isinstance(chapters,list),f"{bid}: chapters must be list")
    cleared = (book.get("rights_status")=="cleared" and work.get("rights_status")=="cleared"
               and bool(book.get("rights_evidence")) and bool(work.get("rights_evidence"))
               and bool(work.get("allowed_to_publish")))
    if chapters or book.get("status")=="available":
        require(cleared,f"{bid}: publishing requires verified rights and evidence")
        require(book.get("status")=="available",f"{bid}: chapters must not be exposed while pending")
        require(bool(chapters),f"{bid}: available book has no chapters")
    if book.get("rights_type") != "original" and chapters:
        require(bool(work.get("source_pin")) and bool(re.fullmatch(r"[a-fA-F0-9]{64}",work.get("source_snapshot_sha256") or "")),
                f"{bid}: licensed translated source must be SHA256-pinned")
    for pos,entry in enumerate(chapters,1):
        raw=entry.get("path","")
        path=Path(raw)
        require(not path.is_absolute() and ".." not in path.parts and len(path.parts)==3 and path.parts[:2]==("data","chapters") and path.suffix==".json",f"{bid}: unsafe chapter path {raw}")
        if path.is_absolute() or ".." in path.parts:continue
        chapter=load(path)
        require(chapter.get("bookId")==bid and chapter.get("chapter")==pos,f"{raw}: book ID/chapter mismatch")
        require(chapter.get("qa_status")=="passed",f"{raw}: editorial QA not passed")
        require(chapter.get("rights_status")=="cleared",f"{raw}: chapter rights unresolved")
        paras=chapter.get("paragraphs",[])
        require(isinstance(paras,list) and bool(paras) and all(isinstance(s,str) and s.strip() for s in paras),f"{raw}: missing/empty prose")
        if not isinstance(paras,list):continue
        annotated=set()
        for d in chapter.get("dialogues",[]):
            ix=d.get("paragraph")
            require(isinstance(ix,int) and ix>=0 and ix<len(paras) and ix not in annotated,f"{raw}: dialogue index invalid/duplicate: {ix}")
            if not isinstance(ix,int) or not (0<=ix<len(paras)): continue
            annotated.add(ix)
            speaker,addr,phase=d.get("speaker"),d.get("addressee"),d.get("phase")
            require(people.get(speaker,{}).get("book_id")==bid and people.get(addr,{}).get("book_id")==bid,f"{raw} #{ix}: speaker/addressee identity unknown")
            match=[r for r in relations if r.get("book_id")==bid and r.get("speaker")==speaker and r.get("addressee")==addr and r.get("phase")==phase and r.get("locked") and pos>=r.get("valid_from_chapter",1) and (r.get("valid_to_chapter") is None or pos<=r["valid_to_chapter"])]
            require(len(match)==1,f"{raw} #{ix}: directed relationship phase missing/ambiguous")
            require(d.get("review_status")=="approved" and bool(d.get("evidence")),f"{raw} #{ix}: dialogue unreviewed")
            if match:
                edge=match[0]
                require(d.get("self_pronoun")==edge.get("self_pronoun") and d.get("address_pronoun")==edge.get("address_pronoun"),f"{raw} #{ix}: PRONOUN DRIFT for {speaker}->{addr} in {phase}")
                quoted=paras[ix]
                require(has_word(quoted,d.get("self_pronoun","")) and has_word(quoted,d.get("address_pronoun","")),f"{raw} #{ix}: pronoun annotation lacks textual evidence")
        for ix,p in enumerate(paras):
            if p.lstrip().startswith(("“","\"","—")):
                require(ix in annotated,f"{raw} #{ix}: direct speech missing annotation")
alias_owner={}
for t in canon.get("terms",[]):
    if not t.get("locked"):continue
    for alias in [t.get("source","")]+t.get("aliases",[]):
        k=alias.casefold()
        require(bool(k), "locked term has empty alias")
        require(k not in alias_owner or alias_owner[k]==t.get("id"),f"Glossary locked-alias conflict: {alias}")
        alias_owner[k]=t.get("id")
if errors:
    print("FAIL: visuNovel publication gate",file=sys.stderr)
    for msg in errors: print(" - "+msg,file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(books)} titles; {sum(len(b.get('chapters',[])) for b in books)} authorized chapters; rights and directed dialogue annotations verified")
