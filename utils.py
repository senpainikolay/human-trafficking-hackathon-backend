import re

def build_search_pattern(words):
    return re.compile(r'\b(?:' + '|'.join(re.escape(word) for word in words) + r')\b', re.IGNORECASE)

def count_word_occurrences(text, pattern):
    matches = re.findall(pattern, text)
    word_count = {}
    for match in matches:
        word_count[match.lower()] = word_count.get(match.lower(), 0) + 1
    return word_count

