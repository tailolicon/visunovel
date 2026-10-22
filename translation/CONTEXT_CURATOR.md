# Context curator — deterministic rules, no invented lore

The source of truth is \`translation/canon.json\` on the current \`main\`. The supporting \`translation/world_bible.json\` is a **source-evidenced lore index**. Both are audited by \`translation/context_lint.py\` and synthetic regression tests in \`tests/test_context_lint.py\`. These tools do **not** read the Korean novel or generate translations.

## Character identity

Use immutable \`characters[].id\` values within a work. Every canonical name and alias belongs to exactly one character **within that work**. Homonymous aliases are blocking until manually disambiguated; normalize Unicode NFKC and casefold for collision checks. Do not conflate an epithet, role, title or narrator label with identity without direct evidence. If the evidence is absent, leave the alias in a review queue and mark it unknown.

## Directed relationships and phases

Every address edge is \`book_id, speaker, addressee, phase, valid_from_chapter, valid_to_chapter, self_pronoun, address_pronoun, evidence, reviewed_by, locked\`. An edge from A to B does **not** authorize B to A. Chapter intervals for the same directed pair must not overlap ambiguously; overlapping phases are allowed only with **distinct explicit \`scene_scope\` values**. Scene-scoped records still need approved transitions when a phase changes in dialogue.

Every approved dialogue records \`paragraph\` (zero-based), \`speaker\`, \`addressee\`, \`phase\`, \`self_pronoun\`, \`address_pronoun\`, \`review_status\`, and \`evidence\`. \`scene\` can override the chapter-level \`scene\` for multi-scene chapters. The validator checks actual quoted speech instead of narration around the quotes. An author may intentionally omit a pronoun: in that case do not fabricate one or mark a false approval; log the exception for manual review and evolve the schema with evidence.

When a pair changes phase, add \`relationship_transitions[]\` with \`book_id\`, \`speaker\`, \`addressee\`, \`from_phase\`, \`to_phase\`, \`chapter\`, \`paragraph\`, optional \`scene\`, \`trigger\`, \`evidence\`, \`reviewed_by\`, and \`review_id\`. The transition must occur between the last observation of the old phase and first observation of the new phase. No approved transition = blocked. The reverse direction requires a **separate** approved transition if its register changes. Do not silently infer it from the first.

## World bible and spoiler guard

A \`confirmed\` fact needs a source reference and reviewer. A \`candidate\` or \`unknown\` fact cannot be locked. \`character_knowledge\` facts also record \`character_id\` and \`known_from_chapter\`. When a dialogue lists \`knowledge_refs\`, the linter rejects knowledge before its first known chapter or by the wrong speaker. This does not prove a line's semantics; it prevents a known category of timeline mistakes.

The two original demo chapters supply three directly observed lore facts. **No** Korean-novel lore is promoted to canon while its source is unavailable and rights status is pending. This is intentionally an empty, explicit world bible for that work, not a claim that its plot is unknown to readers.

## Running checks

\`\`\`sh
python3 translation/context_lint.py
python3 -m unittest discover -s tests -p 'test_context_lint.py' -v
\`\`\`

A passing automated result means the modeled identity, edge intervals, dialogue annotation, and fact timeline are internally consistent. It does **not** certify literary translation quality, authorial intent, copyright status or that all speakers were correctly identified. The independent editorial reviewer must compare licensed source scenes.

## Known limitations and follow-up

- The legacy demo \`canon.json\` has no \`relationship_transitions\` yet, because neither character changes phase in the two existing chapters. Add transitions only with genuine story evidence.
- \`scene_scope\` is an explicit escape hatch for concurrent roles or disguise; the validator does not infer context automatically. An editor must approve each scoped change.
- If a novel chapter uses dialogue with no explicit pronouns, a future version should support reviewed \`pronoun_omitted\` annotations rather than forcing invented wording.
- The existing \`scripts/check.py\` and Pages workflow are separate gates; this context gate runs on its own CI workflow. A release integrator should require **both** gates before publication.
