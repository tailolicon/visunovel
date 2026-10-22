# Vietnamese edition provenance — 2026-10-22

User-selected speech baseline: **only chapters 1–20 at** https://truyenqqko.com/truyen-tranh/su-chuan-muc-cua-ma-vuong-22584 . Do not use later chapters as speech evidence.

## Important edition ambiguity
- The requested TruyenQQKo page was not accessible via the available web reader (DisabledError).
- https://nettruyenar.com/truyen-tranh/su-chuan-muc-cua-ma-vuong-29960 labels its Vietnamese translator group **Phong Vân Võ Lâm**.
- https://www.zettruyen2.com/truyen-tranh/su-chuan-muc-cua-ma-vuong labels its Vietnamese translator group **Bách Diệp Comics**.
- These are site-provided labels, **not independently verified credits**. The sites may have different translation editions or incorrect metadata. Neither listing proves which group translated the user's requested TruyenQQKo chapters.
- https://truyentranhmanhua.org/truyen-tranh/su-chuan-muc-cua-ma-vuong/chap-2 returned a reader HTML shell without accessible panel dialogue; a guessed image URL returned 403.

## Evidence policy
An image from a mirror is NOT assumed identical to the TruyenQQKo version. Record edition ID, visible translation credit/watermark when present, chapter, image URL, exact scene, and source retrieval status. If editions differ in speech, leave the Vietnamese pronoun unresolved rather than choosing the smoother wording.

Current direct Vietnamese panel evidence: **one chapter-1 image on a mirror**, zero additional panels verified in this run, zero new approved A→B/B→A address pairs. All names, glossary entries, and relationship phase changes remain pending independent review.

The separate workflow `.github/workflows/panel-coverage.yml` enforces that index entries and duplicate observations cannot inflate verified image coverage. No comic image or full chapter text is stored in the repository.

## Edition identity guard (2026-10-22)

The user-selected TruyenQQKo URL still returns `DisabledError`. A reader shell for chapter 2 on the alternate mirror was reachable, but **the dialogue images were not actually inspected**. No new Vietnamese speech evidence is approved.

Every observation now carries a `source_edition_id` tied to a declared host and medium. The single chapter-1 panel is explicitly `vn-mirror` with `edition_match_status: unverified`, `selected_baseline_verified: false`, provisional speaker identity, and unknown addressee. English novel/title observations are marked `not_applicable` for Vietnamese edition matching.

The new `edition_provenance_lint.py` rejects missing edition IDs, unrelated image hosts, mirror-as-primary claims, invented selected-source status, and direct-panel approvals without visual-review metadata. This is a **structural metadata gate**, not proof the cited images were examined. Only a future inspection of the selected edition can justify the `selected_baseline_verified` flag. Until then the selected-source panel count is **zero**, while the historical unmatched mirror-panel count is **one**.

`python3 translation/edition_provenance_lint.py` and `python3 -m unittest discover -s tests -p 'test_edition_provenance_lint.py' -v` are part of the panel-coverage CI.
