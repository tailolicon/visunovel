# Five stable translation lanes — private batch allocation

## The user-defined source of context
- The user's context from PR #2 is now on `main`: `translation/CONTEXT_MAWANG.md` and `translation/canon.json`.
- There are **19 candidate profiles** from the Korean novel; all its identities are `locked:false`. There are **15 unresolved proposed directed speech pairs**. These are hypotheses, **not approved xưng hô rules**.
- When translating source text that the user has actually supplied, read relevant canon plus full local scene; preserve its speaker/addressee, register, narrator POV and chronology. Do not hallucinate or auto-lock ambiguous choices. Flag `[CẦN_XƯNG_HÔ]` where needed.
- Do not treat sources and scene-level evidence from the manhwa as novel canon when the two adaptations differ.

## Fixed allocation (no competing chapter writers)

| Lane | Start minute (each hour, Vietnam time) | Wave 0 | Wave 1 | Stable private branch |
|---|---:|---|---|---|
| 1 | :00 | 137–141 | 162–166 | `automation/visunovel-private-lane-1` |
| 2 | :12 | 142–146 | 167–171 | `automation/visunovel-private-lane-2` |
| 3 | :24 | 147–151 | 172–176 | `automation/visunovel-private-lane-3` |
| 4 | :36 | 152–156 | 177–181 | `automation/visunovel-private-lane-4` |
| 5 | :48 | 157–161 | 182–186 | `automation/visunovel-private-lane-5` |

All future waves advance by 25 chapters. `python3 scripts/batch_queue.py --lane 1 --waves 2` calculates assignments deterministically. **Five workers every hour cannot be spaced 20 minutes apart**; five distinct within-hour starts require a 12-minute stride.

## Storage boundary: two repositories

- **Public planning, canon and website**: [tailolicon/visunovel](https://github.com/tailolicon/visunovel), branch `main`. Its existing `automation/visunovel-translate-lane-*` branches are **public and MUST NOT hold book source or private drafts**.
- **Private source and draft storage**: `tailolicon/Translate` (verified **private** on 2026-10-23), in a dedicated `visunovel/` namespace. Existing private repo code on `main` is unrelated and read-only except for future user-provided source deposits. Five workers use only dedicated stable private branches `automation/visunovel-private-lane-N`, not public branch names.
- Private input example: `tailolicon/Translate`, source ref `automation/visunovel-private-source` (user-owned, read-only for workers), path `visunovel/source/the-demon-king-overrun/ch-0137.ko.txt`.
- Upload source chapter files to [the private source branch](https://github.com/tailolicon/Translate/tree/automation/visunovel-private-source/visunovel/source/the-demon-king-overrun) in the pre-created intake folder. Workers READ ONLY from this source branch, not from the private repo's unrelated `main`.
- Verify the output repository is still private on every run. If the private repo or required input is missing, report `waiting_source`; never write to public fallback.

## Chapter source and output boundary
- `translation/batch_plan.json` is the source of truth for allocation; GitHub branch ref plus batch ID are the stable work identity.
- A translation unit must have **actual user-supplied complete source chapter text**, e.g. `visunovel/source/the-demon-king-overrun/ch-0137.ko.txt` in user-managed **private** storage. A website URL, summary, Korean title, context note or manga handoff does not fulfill this condition.
- Each lane checks its assigned sources and existing output/status before starting. **If missing, mark `waiting_source`; do not scrape third-party novels, invent a chapter, or claim work was translated.**
- Draft only for personal use from user-provided text; retain privately, outside public Pages and any public artifact. Confirm the target repo or storage is private before saving. Do not store raw source in `main`, GitHub Actions artifact, Pages output or another public location.
- Serialize inside each lane by chapter, then checkpoint on the same stable branch: `work/private_drafts/lane-N/ch-XXXX.vi.md`, `ch-XXXX.qa.json`. Include original language, source checksum, pinned canon blob SHA, source location, coverage/paragraph counts and `review_status:needs_review`. Never mark `passed` based only on a model's self-check.
- **Do not commit draft translations when the source is unavailable or rights/access assumptions are unverified.** Do not change `rights_status`, `allowed_to_publish`, or public `data/library.json` without evidence of web redistribution rights.

## Correctly separated worker execution
1. Verify `main`, the user's source location, `translation/batch_plan.json`, `translation/canon.json` and the lane's **existing** branch. If the lane branch is missing, create it once using the verified base SHA; never create a fresh timestamp branch every hourly run.
2. The worker may edit only its own `visunovel/work/private_drafts/lane-N/**` plus its own `visunovel/visunovel/work/status/lane-N.json`. Other lanes' branches, shared canon and main are read-only.
3. Select the lowest-numbered source-available chapter in its own current batch that is not already at `needs_review`/QA-approved status. Advance only after audit; never translate a chapter twice simply because another run began.
4. Respect current source SHA256 and pinned canon hash. If a draft exists with mismatched hashes, flag stale for re-review; do not overwrite silently.
5. Commit small checkpoints to the same lane branch with expected SHA / compare-and-swap. If the branch changed, refetch and reconcile. **Never force push**.
6. A **separate editorial integrator** must review all lanes and plot chronology. A lane never approves its own draft, edits public catalog or merges its own PR. There is no automatic novel publication.
7. Report work attempted, chapters source-available, chapters actually drafted, QA blockers, branch SHA and next chapter. If no chapter source exists, report that plainly; improve tests or reader privately instead of fabricating progress.

## Current known blocker (2026-10-23)
`main` currently contains **context but no user-provided Korean novel chapter text**. Therefore the automated workers cannot legitimately translate any chapter until a real source text is added to an authorized private input location, or provided directly by the user.
