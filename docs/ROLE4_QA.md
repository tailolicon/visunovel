# Independent QA — Role 4

This lane is independent of the translation engine and never fetches the Korean novel. It accepts user-supplied source and draft text, and optional reviewed dialogue annotations. It detects missing/duplicate paragraphs, number changes, untranslated Hangul, unresolved markers, locked glossary drift, directed-pronoun drift and unreviewed phase transitions.

Output contains only hashes, counts and issue codes, stored in a private local folder. A clean structural report is always `needs_review`, never `passed`: meaning, fluency, narrator POV, names and relationships require human comparison with an authorized source. No public release is authorized by this tool.

Run `python3 tools/independent_qa.py path/to/source.txt path/to/draft.vi.txt --chapter 137` and optionally `--annotations private/dialogues.json`. The draft and source are not uploaded. `--report` must stay under `~/.local/share/visunovel-private/`.
