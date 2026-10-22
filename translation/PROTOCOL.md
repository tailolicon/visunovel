# visuNovel — translation & editorial canon protocol
Version: 1 (2026-10-22). Inspired by the **architecture**, not the protected corpus, of [hachimi-tl-vi](https://github.com/tailolicon/hachimi-tl-vi): \`CONTEXT_MAINTENANCE.md\`, \`PARALLEL_TRANSLATION.md\`, \`TRANSLATION_REVIEW.md\`, \`WORKER_CONTINUOUS.md\`.

## 0. Legal and source gate — FAIL CLOSED
- Translating a third-party novel for publication is a separate right from reading it; website access, purchase, free preview, scraped chapters, fan-made translation and attribution DO NOT constitute distribution permission.
- Before a source is consumed as translation input, record owner, explicit translation license/public-domain basis, permitted geography/media, a stable copy of the authorized source, source version/checksum, evidence URL/document and expiration. The legal owner must allow online redistribution of the translated content, not merely private reading.
- For \`마왕인데 용사가 너무 많음\` the **public distribution right is PENDING**. Do not download, mirror or publish complete chapters from external websites. An actual chapter text **supplied by the user** may be transformed into a draft **for private use** in a private repository or local environment; do not assume that authorizes redistributing it. No source text or translated drafts go to the public visuNovel repo, its Pages build or Actions artifacts. The public publication gate remains STOP until separately licensed and documented.
- Original visuNovel demo copy is owned by the project. Never mislabel the demo as the Korean novel.

## 1. Canonical files and trust
\`translation/canon.json\` on \`main\` is authoritative for characters, directed relationships, phases, reviewed terminology and source pins. Chat history and workers' private memories are not authority. Current translations are hypotheses; they do not prove the rule. Every accepted change references a reviewer and source-scene evidence.

Precedence: **explicit scene/source evidence** > **locked relationship for that pair and phase** > **locked names/terms** > **reviewed observed memory** > **general literary voice rules**. Scene overrides need a recorded \`evidence\`, \`reason\`, \`chapter\`, \`reviewer\`, and a bounded scope. Unknown is never default; do not invent missing names, ages, power relationships or inferred intimacy.

## 2. Character and address system — non-negotiable
- Stable character ID, aliases, names, titles, relations, origin, personality, speaking style, and knowledge timeline are distinct fields.
- A relationship is **directed**: \`A -> B\` and \`B -> A\` require independent records; never assume symmetry.
- For every chapter and scene, record \`speaker_id\`, \`addressee_id\`, narrative \`phase\`, \`scene_id\`, \`self_pronoun\`, \`address_pronoun\`, honorifics and change trigger. For instance, an elder might use \`ta/ngươi\` in public but \`tôi/anh\` in a private cover identity. This is two reviewed contextual states, not random variation.
- Keep the same terms of address **across adjacent paragraphs, chapters and worker sessions**, until an evidence-backed event authorizes transition: promotion, revelation, family discovery, rupture, disguise, ceremony or conscious code-switching.
- Within the same scene an actual quoted utterance can override the phase rule only with direct textual evidence and editorial sign-off. Automatic alternation \`ta/tôi\`, \`ngươi/anh\`, \`hắn/gã/anh ta\` for stylistic variety is forbidden when referents or relationship signals change.
- Author pronouns are perspective-dependent: first-person narration, interior monologue, third-person narration and direct speech use separate voice tracks; do not impose dialogue pronouns on narrator.
- On unresolved speaker/addressee or relation, use \`defer\` for manual/editorial resolution; never publish a guessed relationship.

### Dialogue annotation required before public QA
Each direct-speech paragraph in a chapter JSON needs one \`dialogues[]\` entry: \`paragraph\` (zero-based), \`speaker\`, \`addressee\`, \`phase\`, \`self_pronoun\`, \`address_pronoun\`, \`review_status=approved\`, \`evidence\`. Validation checks consistency against the directed phase registry. It is a **guard**, not a substitute for semantic review.

## 3. Translation unit and context window
1. Identify narrative arc, chapter index, scene/time, narrator POV, who is present, and who knows which secret at that moment. Do not leak later plot reveals backward.
2. Load pinned source (rights cleared), preceding 2 scenes, following 1 scene when available, chapter synopsis, relevant character records and directed address edges; preserve page/chapter numbers.
3. Select only glossary terms referenced by this batch and high-confidence reviewed speech samples. Context extraction may discover new candidates but they enter \`term_review_queue\`, **not** locked glossary.
4. Draft faithful fluent Vietnamese; keep tense/aspect, honorific subtext, ambiguity, humor, pacing, metaphors and plot clues. Do not pad sentences to sound ornate. Korean names/titles may have multiple sensible forms: check identity and social setting before choosing.
5. Run independent pass: source semantic comparison, cross-scene pronoun audit, named-entity/glossary audit, natural Vietnamese read-only pass, numeric/markup/paragraph structure checks, duplicate/missing lines and leakage of untranslated phrases.
6. Register unresolved items as blocking \`defer\` issues with context, not silent approximations. Keep all quotes and source evidence within licensed storage.

## 4. State machine (proposed worker API)
\`not_authorized -> rights_verified -> context_ready -> claimed -> drafted -> audited -> approved -> published\`.

- One work unit = a chapter, with one claim owner and expiring lease. Workers create a claim atomically, refresh heartbeat and write checkpoints; takeover only after actual expiration and revision check.
- Draft/review results are placed in worker-owned paths. No worker writes release content directly; one serialized integration lane checks live source SHA, canonical hash and approvals before merging.
- All writes use live blob SHA / expected commit; never force push or overwrite another worker. Report exact commit and QA results. A claim race causes selection of another unit, not collision.
- A change in canon or source checksum invalidates affected chapter QA for re-review; unrelated reviewed chapters remain valid.
- If no authorized source chapters exist: maintain web, editorial schema, tests, accessibility, performance and documentation; do not fabricate translations or reinterpret license limits.

## 5. Release gate
A chapter is publishable only if all are true:
- work \`rights_status=cleared\`, rights evidence recorded, and permission explicitly covers translated web publication;
- exact source snapshot pinned (\`source_pin\`, SHA256 for third-party licensed original);
- translated chapter has source alignment and complete text; QA passed;
- all dialogue speakers and addressees resolve to stable IDs; all directed pronoun edges match phases or have approved scoped override;
- all locked terms match; no unreviewed terminological collision;
- style, structural and semantic audits passed;
- integration lane merges after verifying the latest \`main\`.

## 6. What NOT to reuse from Hachimi
Do not copy game corpus, game glossary, character identity registry, or anime-specific speech profiles. Reuse the **policy pattern**: pinned provenance, evidence-led canon, relevance-filtered prompts, review queue, no silent promotion, crash-safe claims, deterministic QA and serial merges.

## 7. Engineering note
The initial website includes a production-minded validator and example story, **not** a fully automated translator or licensing mechanism. A model provider, encrypted secrets, authorized source import and durable job dispatcher must be added before autonomous translation can run.