import re

def paragraphs(text):
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

def inspect(source, draft):
    issues = []
    if len(paragraphs(source)) != len(paragraphs(draft)):
        issues.append('PARAGRAPH_COUNT')
    if '[CẦN_XƯNG_HÔ]' in draft:
        issues.append('PRONOUN_UNRESOLVED')
    if len(draft.strip()) < max(8, len(source.strip()) // 9):
        issues.append('SUSPICIOUSLY_SHORT')
    return issues
