#!/usr/bin/env python3
"""Reject unexpected files in the public GitHub Pages artifact."""
import json
import sys
from pathlib import Path

def validate(root: Path):
    errors = []
    if not root.is_dir():
        return ["Public build directory missing"]
    expected = {"index.html", "personal.html", ".nojekyll", "data/library.json"}
    try:
        library = json.loads((root / "data/library.json").read_text(encoding="utf-8"))
        for book in library.get("books", []):
            for chapter in book.get("chapters", []):
                path = chapter.get("path", "")
                if not isinstance(path, str) or not path.startswith("data/chapters/") or not path.endswith(".json") or ".." in Path(path).parts:
                    errors.append("Unsafe chapter path in library")
                else:
                    expected.add(path)
    except (OSError, ValueError, TypeError):
        errors.append("Cannot read public library metadata")
    for file in root.rglob("*"):
        if file.is_symlink():
            errors.append("Symlink in public artifact")
            continue
        if not file.is_file():
            continue
        rel = file.relative_to(root).as_posix()
        if rel.startswith("assets/") and file.suffix in {".js", ".mjs", ".css"} and len(Path(rel).parts) == 2:
            expected.add(rel)
        if rel not in expected:
            errors.append("Unexpected public artifact: " + rel)
    for path in expected:
        if not (root / path).is_file():
            errors.append("Missing public artifact: " + path)
    return errors

if __name__ == "__main__":
    issues = validate(Path(sys.argv[1] if len(sys.argv) > 1 else "public-build"))
    if issues:
        for issue in issues:
            print("FAIL: " + issue, file=sys.stderr)
        raise SystemExit(1)
    print("PASS: public artifact contains only frontend and approved library entries")
