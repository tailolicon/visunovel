#!/usr/bin/env python3
"""Provenance gate for bounded comic evidence; never auto-promote to translation canon."""
from __future__ import annotations
import json,sys
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
ALLOWED_MEDIA={"manhwa_vi_panel","manhwa_english_chapter_title","novel_english_secondary"}
ALLOWED_GRADES={"panel_observed","chapter_title_observed","chapter_text_observed"}
ALLOWED_APPROVAL={"scene_only","candidate","cross_medium_only","needs_vietnamese_panel","needs_scene_panel_and_outcome"}
BLOCKED_FIELDS={"full_text","source_text","translated_text","page_images","chapter_html"}

def is_url(s:object)->bool:
    if not isinstance(s,str):return False
    parsed=urlparse(s)
    return parsed.scheme=="https" and bool(parsed.hostname)

def validate(data:dict, canon:dict|None=None, bible:dict|None=None)->list[str]:
    errors=[]
    def err(s:str)->None:errors.append(s)
    if data.get("book_id")!="the-demon-king-overrun":err("wrong book_id")
    if data.get("scope",{}).get("vn_manhwa_chapters_in_scope")!=[1,20]:err("manga evidence must stay within chapters 1–20")
    if data.get("scope",{}).get("novel_secondary_chapters_in_scope")!=[1,20]:err("secondary novel evidence must stay within chapters 1–20")
    if data.get("editorial_release_gate")!="NOT_READY_FOR_CANON_LOCK":err("incomplete evidence cannot authorize canon lock")
    if not is_url(data.get("requested_source")):err("requested source URL missing")
    names={}
    for i,candidate in enumerate(data.get("candidate_identities",[])):
        loc=f"identity[{i}]"
        cid=candidate.get("id")
        if not cid or cid in names:err(loc+": missing/duplicate candidate ID")
        if candidate.get("name_locked") is not False or candidate.get("pronoun_locked") is not False:err(loc+": candidate must not be locked")
        if not candidate.get("observed") or not all(isinstance(x,str) and x.strip() for x in candidate["observed"]):err(loc+": missing observed spelling")
        if not candidate.get("sources") or not all(is_url(x) for x in candidate["sources"]):err(loc+": missing source URLs")
        names[cid]=candidate
    ids=set()
    for i,obs in enumerate(data.get("observations",[])):
        loc=f"observation[{i}]"
        oid=obs.get("id")
        if not oid or oid in ids:err(loc+": missing/duplicate ID")
        ids.add(oid)
        if obs.get("medium") not in ALLOWED_MEDIA:err(loc+": unsupported evidence medium")
        ch=obs.get("chapter")
        if isinstance(ch,bool) or not isinstance(ch,int) or not 1<=ch<=20:err(loc+": chapter outside 1–20")
        if not is_url(obs.get("source_url")):err(loc+": invalid provenance URL")
        if obs.get("evidence_grade") not in ALLOWED_GRADES:err(loc+": invalid grade")
        if obs.get("approval") not in ALLOWED_APPROVAL:err(loc+": requires separate editorial approval")
        if obs.get("locked") is True:err(loc+": cannot lock observations")
        if obs.get("medium")=="manhwa_vi_panel":
            if obs.get("evidence_grade")!="panel_observed" or not is_url(obs.get("chapter_url")):err(loc+": visual evidence requires panel and chapter URLs")
        elif obs.get("evidence_grade")=="panel_observed":err(loc+": non-panel cannot claim visual verification")
        for id_ in obs.get("about",[]):
            if id_ not in names:err(loc+f": unidentified candidate {id_}")
        if not isinstance(obs.get("claim_vi"),str) or len(obs["claim_vi"])>500:err(loc+": missing or overlong evidence summary")
        if any(k in obs for k in BLOCKED_FIELDS):err(loc+": no original panels/chapter text permitted")
    if not ids:err("no source observations")
    if canon is not None:
        # The pending ledger cannot silently promote names, glossary or phases.
        for section in ("characters", "terms", "relationship_transitions"):
            for idx, item in enumerate(canon.get(section, [])):
                if item.get("book_id") == data.get("book_id") and (
                    item.get("locked") is True or section == "relationship_transitions"
                ):
                    err(f"{section}[{idx}]: pending evidence cannot authorize canon promotion")
        for i,row in enumerate(canon.get("relationship_review_queue",[])):
            if row.get("book_id")!=data.get("book_id"):continue
            loc=f"queue[{i}]"
            if row.get("source_evidence_id") not in ids:err(loc+": evidence reference missing")
            if row.get("speaker_candidate") not in names or row.get("addressee_candidate") not in names:err(loc+": unknown party candidate")
            if row.get("locked") or row.get("review_status")=="approved" or row.get("proposed_self_pronoun") is not None or row.get("proposed_address_pronoun") is not None:
                err(loc+": unreviewed candidate was promoted or assigned pronouns")
        if any(p.get("book_id")==data.get("book_id") and p.get("locked") for p in canon.get("relationships",[])):
            err("cannot lock literary relationship from this unreviewed evidence ledger")
    if bible is not None:
        for i,fact in enumerate(bible.get("facts",[])):
            if fact.get("book_id")!=data.get("book_id"):continue
            if fact.get("locked") or fact.get("status")!="candidate":err(f"world_bible[{i}]: literary candidate must remain unlocked")
    return errors

def main()->int:
    try:
        ledger=json.loads((ROOT/"translation/evidence_01_20.json").read_text(encoding="utf-8"))
        canon=json.loads((ROOT/"translation/canon.json").read_text(encoding="utf-8"))
        bible=json.loads((ROOT/"translation/world_bible.json").read_text(encoding="utf-8"))
    except (OSError,ValueError) as e:
        print(f"FAIL: cannot load evidence inputs: {e}",file=sys.stderr);return 1
    problems=validate(ledger,canon,bible)
    if problems:
        print("FAIL: evidence provenance",file=sys.stderr)
        for problem in problems:print(" - "+problem,file=sys.stderr)
        return 1
    print(f"PASS: {len(ledger['observations'])} evidence pointers; {len(ledger['candidate_identities'])} unapproved identity candidates; no invented pronoun locks")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
