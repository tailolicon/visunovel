# Role 4 — independent private QA

The user's preferred speech baseline is **Vietnamese manhwa chapters 1–20 of Sự Chuẩn Mực Của Ma Vương on TruyenQQKo**. Later Vietnamese chapters are explicitly rejected as a naming/pronoun authority. Only **one** Vietnamese image (chapter 1, panel 11, an alternative mirror) has been visually checked, **zero** from the selected TruyenQQKo edition. English novel and comic listings are cross-medium candidates, not Vietnamese speech evidence. See \`translation/EVIDENCE_01_20.md\` and \`translation/evidence_01_20.json\`.

## Local-only structural QA

\`\`\`sh
python3 translation/independent_qa.py \
  /path/outside/repo/user-source-ch137.txt \
  /path/outside/repo/private-draft-ch137.vi.txt \
  --book-id the-demon-king-overrun --chapter 137
\`\`\`

Both inputs must be **local TXT/MD files explicitly supplied by the user** and located outside the repository. There are no network calls. No chapter text or translation is saved to the repository, uploaded to Pages, or printed. Metadata reports go exclusively to \`~/.local/share/visunovel-private/qa/\` (mode 0700 for the directory, 0600 for each report). Existing reports cannot be overwritten; use a new filename for a new run. The report records SHA256 hashes, paragraph counts, stable issue codes and publication blockers, not story text.

A structural result \`PASS_STRUCTURAL_ONLY\` is **not** a translation-quality approval. Literary status is always \`NOT_REVIEWED\` and public release always \`BLOCKED\`. The rights record for the third-party novel remains pending; that is reported separately as \`release_blockers\`, not confused with whether private structural checks succeeded. No full text may be copied into GitHub or GitHub Pages.

## Optional directed dialogue reviews

A local JSON manifest can include \`dialogue_reviews\` for each independently inspected utterance:

\`\`\`json
{
  "book_id": "example-original-demo",
  "chapter": 137,
  "source_sha256": "<sha256-of-normalized-user-source>",
  "qa_status": "needs_review",
  "draft_only": true,
  "public_release_authorized": false,
  "dialogue_reviews": [
    {
      "paragraph": 0,
      "speaker": "stable-A-id",
      "addressee": "stable-B-id",
      "phase": "scene-specific-phase",
      "self_pronoun": "em",
      "address_pronoun": "chị",
      "source_scene_ref": "local chapter and paragraph/panel evidence",
      "reviewed_by": "editor",
      "review_id": "review-unique-id",
      "review_status": "pending"
    }
  ]
}
\`\`\`

For \`approved\` dialogue entries the gate requires a uniquely matching **locked directed edge** for exactly A→B, chapter, phase and scene, plus scene evidence and reviewer metadata. It does not infer B→A, does not convert English honorifics into Vietnamese pronouns, and does not auto-promote candidates. A missing or pending review is surfaced as a warning. **Even approved annotations in a synthetic demo do not make the full chapter publication-ready**.

## CI checks

\`\`\`sh
python3 -m unittest discover -s tests -p 'test_independent_qa.py' -v
python3 translation/evidence_lint.py
python3 translation/edition_provenance_lint.py
python3 translation/context_lint.py
\`\`\`

Role 4's CI uses only original/synthetic fixtures and never loads the novel. The tests cover source checksum, chapter identity, paragraph mismatch, missing review, wrong direction, phase drift, false approval, private path enforcement, symlinks, report permissions and overwrite prevention. Role 2 owns the character canon and provenance ledger; Role 4 only consumes them.
