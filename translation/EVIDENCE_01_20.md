# First 20 chapters: bounded evidence, not fabricated canon

## User's selected baseline
Requested: [TruyenQQKo's Sự Chuẩn Mực Của Ma Vương](https://truyenqqko.com/truyen-tranh/su-chuan-muc-cua-ma-vuong-22584) **chapters 1–20 only**. Dialogue/terminology after manhwa chapter 20 **must not** become editorial evidence because the later Vietnamese translation quality has been rejected by the reader.

The requested site returned a **DisabledError** through the available web reader on 2026-10-22. That is a retrieval limitation, not permission to pretend the pages were examined. An alternative Vietnamese mirror of chapter 1 yielded one actual visual panel. The English comic listing exposed chapter titles, and English *novel* chapters 1, 2, 5, 6, 9, 12, 19, and 20 were read for **cross-medium corroboration only**. Comic chapter numbers and novel chapter numbers are not interchangeable.

## Evidence status
All ten source observations and six name variants are in \`evidence_01_20.json\`. The only directly inspected Vietnamese image is the first chapter's panel no. 11. It establishes a **scene-specific** use of *ta* by the wounded dragon-scale speaker; the Berze identification is still contingent on cross-medium mapping. Nothing here verifies the rest of the Vietnamese chapters, or the full dialogue style of an A→B pair.

Primary unresolved name forms: \`Berge/ Berze Deias\`, \`Ernan/Ernyan\`, \`Logger/Logar\`, \`Drakson/Draxon\`. Treat variants as candidates, **not automatically identical or globally locked aliases**. The confirmed social roles in early *English translated novel* scenes can help review, but cannot by themselves dictate Vietnamese honorifics.

## Directed pair review queue
\`canon.json\` currently records eight review requests with source evidence links. They have **no** \`self_pronoun\` / \`address_pronoun\` values and cannot be promoted until a reviewer identifies a concrete dialogue panel, speaker, addressee, relationship phase and its context. A main character's first-person \`ta\` in one scene is not a reason to use \`ta\` in every scene.

## Review procedure
1. Review the specific VN panels 1–20 (or a source with explicit authorized dialogue), independently verify names and speech attribution, and record evidence at chapter + panel + scene granularity.
2. Compare the original Korean or another reliable version **only when needed**, recording disagreements rather than hiding them. Do not assume English translator's titles are the accepted Vietnamese rendering.
3. Approve names and identities separately from directed pronouns. Every approved \`A→B\` must be grounded independently of \`B→A\`.
4. For temporal role changes, first confirm the outcome and the exact chapter; only then write an approved \`relationship_transitions\` event.
5. Until verified, the translation pipeline must surface \`[CẦN_XƯNG_HÔ]\` or defer rather than guess.

## Checks
\`\`\`sh
python3 translation/evidence_lint.py
python3 -m unittest discover -s tests -p 'test_evidence_lint.py' -v
python3 translation/context_lint.py
\`\`\`
The CI evidence gate rejects data outside the chapter boundary, false visual provenance, missing source references, and premature character/glossary/pronoun locks. This is editorial evidence metadata only; no comic art, source novel chapters or derivative translations were copied into the repo.
