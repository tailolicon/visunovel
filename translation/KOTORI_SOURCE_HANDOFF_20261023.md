# Kotori source handoff located — comic chapter 3

User reported the manga images/source were submitted to [tailolicon/manga-tl-factory](https://github.com/tailolicon/manga-tl-factory). Direct GitHub inspection on 2026-10-23 confirmed a **Kotori handoff metadata JSON** in that repository at commit `2204be6f`.

- Upstream: [source_handoff.json](https://github.com/tailolicon/manga-tl-factory/blob/main/work/imports/s-chu-n-m-c-c-a-ma-v-ng/kotori-9602-mvju70ma/source_handoff.json)
- Original reader: https://doctruyen3qhub.fit/truyen-tranh/su-chuan-muc-cua-ma-vuong/20622
- Only chapter currently resolved: **3**; exactly **186** ordered image URLs in the handoff. Chapter ID: `3504262`. Images originate from `s15.anhvip.xyz`.
- [Acquisition test run](https://github.com/tailolicon/manga-tl-factory/actions/runs/39826220023): was **in progress** when initially inspected. Inspect the run's `fetch_result.json` artifact to determine how many images were actually fetched and verified.
- No directly inspected page content from this new handoff yet; do not claim any newly verified lines or character A→B pronouns. Separately, `evidence_01_20.json` has one unmatched Vietnamese mirror page from chapter 1; do not merge provenance or assume matching translation editions.
- Chapters **1–2 and 4–20** still lack Kotori handoffs at this observed commit. Existing comic chapter 1–20 restrictions continue; later comic chapters are explicitly excluded from speech canon.

## Reviewer handoff for character context
1. Use the handoff's source chapter URL and exact page ordinal to identify a panel. Verify the image was actually retrieved, signature/dimensions and visible speaker.
2. Inspect only the relevant dialogue panels (not bulk store artwork in `visunovel`); record scene ID, character stable identity hypothesis, speaker, addressee, and the actual words used.
3. Check the comic edition/translation credit: the user-selected primary earlier was TruyenQQKo; DocTruyen3Q may be a distinct Vietnamese version.
4. Candidate evidence should go to a review queue, with panel URL, editorial reviewer and uncertainty. Independently lock directed `A→B` / `B→A` only after identity and relation phase have been proven.
5. Do not use novel-chapter numbers as if interchangeable with comic chapters.

No image files, chapters, full translated dialogue or copyright material are stored in this commit.