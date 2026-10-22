#!/usr/bin/env python3
"""Pure deterministic 5-lane chapter-batch allocator. Does not fetch source texts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "translation" / "batch_plan.json"

def check_plan(plan):
    start, size, workers = (plan[k] for k in ("chapter_start", "batch_size", "worker_count"))
    if not all(isinstance(n, int) and not isinstance(n,bool) and n>0 for n in (start,size,workers)):
        raise ValueError("chapter_start/batch_size/worker_count must be positive integers")
    if plan["wave_size"] != size*workers:
        raise ValueError("wave_size must equal batch_size * worker_count")
    if sorted(plan["hourly_minute_offsets"]) != list(plan["hourly_minute_offsets"]):
        raise ValueError("hourly slots must be sorted")
    if len(set(plan["hourly_minute_offsets"])) != workers or any(n<0 or n>=60 for n in plan["hourly_minute_offsets"]):
        raise ValueError("one distinct minute slot per lane is required")
    lanes = plan["lanes"]
    if len(lanes)!=workers or [v["id"] for v in lanes] != list(range(1,workers+1)):
        raise ValueError("lane ids must be consecutive, from 1")
    for lane in lanes:
        if lane["first_chapter"] != start + size*(lane["id"]-1):
            raise ValueError("first chapter does not match lane assignment")
        if not lane["branch"].endswith("-"+str(lane["id"])):
            raise ValueError("stable branch must correspond to lane id")

def get_plan():
    p=json.loads(PLAN.read_text(encoding="utf-8"))
    check_plan(p)
    return p

def owner(chapter, plan):
    if chapter < plan["chapter_start"]:
        raise ValueError("chapter is outside translation priority arc")
    return ((chapter - plan["chapter_start"]) // plan["batch_size"]) % plan["worker_count"] + 1

def batch(lane, wave, plan):
    if not 1 <= lane <= plan["worker_count"] or wave < 0:
        raise ValueError("invalid lane/wave")
    first = plan["chapter_start"] + wave*plan["wave_size"] + (lane-1)*plan["batch_size"]
    chapters=list(range(first,first+plan["batch_size"]))
    assert all(owner(c,plan)==lane for c in chapters)
    return {"lane":lane,"wave":wave,"first":first,"last":chapters[-1],"chapters":chapters,
            "branch":plan["lanes"][lane-1]["branch"],
            "folder":plan["lanes"][lane-1]["folder"]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane",type=int)
    parser.add_argument("--waves",type=int,default=2)
    parser.add_argument("--owner",type=int,help="Find exclusive owner lane for a chapter")
    args=parser.parse_args()
    p=get_plan()
    if args.owner is not None:
        print(json.dumps({"chapter":args.owner,"lane":owner(args.owner,p)}))
    else:
        if args.lane is None or args.waves <= 0 or args.waves>1000:
            parser.error("--lane and a positive --waves (<=1000) required")
        print(json.dumps([batch(args.lane,n,p) for n in range(args.waves)],ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
