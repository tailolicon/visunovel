def permitted(canon, book_id):
    return any(w.get('book_id') == book_id and w.get('rights_status') == 'cleared' and w.get('allowed_to_translate') is True for w in canon.get('works', []))
