import re
from pymorphy3 import MorphAnalyzer
from categories import get_combined_category_map

morph = MorphAnalyzer()

def parse_message(text: str):
    match = re.match(r"(\d+)\s+(.+)", text.strip())
    if not match:
        return None, None, None
    amount = int(match.group(1))
    comment = match.group(2).lower()

    category = match_category(comment)
    return amount, comment, category

def match_category(comment: str):
    words = comment.split()
    lemmas = [morph.parse(w)[0].normal_form for w in words]
    category_map = get_combined_category_map()
    for lemma in lemmas:
        if lemma in category_map:
            return category_map[lemma]
        return None