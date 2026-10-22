"""Guarded CLI for user-provided local draft files."""
import json
from pathlib import Path
import personal_translate as translator
import private_context as context
from role3_rights import permitted

original = translator.translate

def guarded(args):
    if not args.dry_run:
        canon = json.loads((translator.ROOT / 'translation/canon.json').read_text(encoding='utf-8'))
        if not permitted(canon, args.book_id):
            raise ValueError('Translation rights are not cleared')
        source = Path(args.input).expanduser().resolve(strict=True)
        if source.is_relative_to(translator.ROOT):
            raise ValueError('Move input outside the repository')
        target = args.output or (translator.PRIVATE_HOME / f'{args.book_id}-chapter-{args.chapter}.vi.txt')
        context.private_path(target)
        context.private_path(translator.PRIVATE_HOME / 'checkpoints' / f'{args.book_id}-chapter-{args.chapter}.json')
    return original(args)

translator.translate = guarded
if __name__ == '__main__':
    raise SystemExit(translator.main())
