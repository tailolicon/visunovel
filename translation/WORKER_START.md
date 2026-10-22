# visuNovel — Stateless autonomous worker start

Each run must inspect live \`main\`, especially \`README.md\`, \`translation/PROTOCOL.md\`, \`translation/canon.json\`, \`data/library.json\`, \`scripts/check.py\`, and existing GitHub Actions results. Do not use previous chat as authoritative state.

## Universal fail-closed constraints
1. Do not fetch, translate or publish the Korean novel (or any third-party full text) unless a verified rights record expressly covers adaptation/translation and web redistribution. Pending is STOP for literary material, NOT for website and QA work.
2. Never remove the legal gate, hide source attribution, reclassify third-party material as original, or set a QA flag to passed without evidence.
3. Do not reassign a character's relation or honorific because the Vietnamese variant sounds more elegant. Record evidence and an approved phase transition.
4. Do not change GitHub Pages settings, repository visibility, billing, or secrets without owner approval. If a publishing step is blocked by access/settings, report the exact blocker.
5. Use small testable commits; no force push. Read live SHAs and rebase/refetch on conflict.

## Five non-overlapping private translation batches (hourly at minutes 00/12/24/36/48)
- **Lane 1:** chapters 137–141, then 162–166, then +25 per wave; own stable branch and private drafts only.
- **Lane 2:** chapters 142–146, then 167–171, then +25 per wave; own stable branch and private drafts only.
- **Lane 3:** chapters 147–151, then 172–176, then +25 per wave; own stable branch and private drafts only.
- **Lane 4:** chapters 152–156, then 177–181, then +25 per wave; own stable branch and private drafts only.
- **Lane 5:** chapters 157–161, then 182–186, then +25 per wave; own stable branch and private drafts only.

**Always read `translation/WORKER_BATCHES.md` and `translation/batch_plan.json` before work.** User-supplied full text is a prerequisite for a private draft; contextual notes/URLs do not count. Five hourly starts must be 12 minutes apart, since five workers cannot each start 20 minutes apart in an hour. Existing language/story candidates are not locked: defer unknown pronouns to review.

Do not create five concurrent \`main\` writers. Each role owns its work or feature branch, and commits to the branch after verifying there is no conflicting editor; release integration is serialized. If direct GitHub mutation is unavailable, provide a specific patch/change report instead of claiming it was committed.

## Output contract each run
Write a concise report: role, current repo head SHA, work unit, actual changed files/commit, checks run, blockers, next eligible task. If nothing legally actionable exists, improve general platform quality and truthfully say no chapter was translated.