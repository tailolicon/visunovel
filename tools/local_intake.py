#!/usr/bin/env python3
"""Record a local user-provided reading file by checksum without copying it.

No web access, no model calls, no GitHub uploads, no rights clearance.
Only a local manifest is written under ~/.local/share/visunovel-private.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE = Path.home() / ".local" / "share" / "visunovel-private"
BOOK = "the-demon-king-overrun"
MAX_BYTES = 1024 * 1024

def under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False

def inspect(path: Path) -> dict:
    path = path.expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
        raise ValueError("Cần tệp văn bản .txt hoặc .md có sẵn trên máy")
    if under(path, ROOT):
        raise ValueError("Không đưa tệp cá nhân vào trong repository; hãy di chuyển ra thư mục riêng")
    size = path.stat().st_size
    if size < 1 or size > MAX_BYTES:
        raise ValueError("Tệp rỗng hoặc vượt giới hạn 1 MiB")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return {"source_basename":path.name, "source_sha256":digest.hexdigest(), "source_bytes":size}

def record(path: Path, chapter: int, private_root: Path, dry_run: bool = False) -> dict:
    if type(chapter) is not int or chapter < 137:
        raise ValueError("Ưu tiên novel chương 137 trở đi; chương trước để sau")
    meta = inspect(path)
    if under(private_root, ROOT):
        raise ValueError("Thư mục lưu manifest riêng tư không được nằm trong repository")
    manifest = {
        "schema_version":1,"book_id":BOOK,"novel_chapter":chapter,
        "source_origin":"user_supplied_local_text",
        "personal_reading_only":True,
        "public_distribution_authorized":False,
        "public_translation_authorized":False,
        "source_sha256":meta["source_sha256"],
        "source_basename":meta["source_basename"],
        "source_bytes":meta["source_bytes"],
        "review_status":"private_unreviewed",
        "privacy_note":"Only metadata is recorded; the source file remains where you placed it.",
    }
    target = private_root.expanduser().resolve() / "intake" / f"{BOOK}-chapter-{chapter}.json"
    if dry_run:
        return {"manifest_path":str(target),"dry_run":True,"manifest":manifest}
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing.get("source_sha256") != meta["source_sha256"]:
            raise ValueError("Đã có bản nhập chương khác hash; không tự ghi đè")
        return {"manifest_path":str(target),"reused":True,"manifest":existing}
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(target.parent, 0o700)
    except OSError:
        pass
    manifest["recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {"manifest_path":str(target),"reused":False,"manifest":manifest}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Tệp .txt/.md do bạn cung cấp")
    parser.add_argument("--chapter", type=int, default=137)
    parser.add_argument("--private-dir", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = record(args.input, args.chapter, args.private_dir, args.dry_run)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"manifest_path":result["manifest_path"],
                      "dry_run":args.dry_run,
                      "source_sha256":result["manifest"]["source_sha256"],
                      "chapter":args.chapter,
                      "public_distribution_authorized":False}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
