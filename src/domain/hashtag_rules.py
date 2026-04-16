import re
from typing import Set

HASHTAG_PATTERN = re.compile(r"(?<!\w)#(\w+)", flags=re.ASCII)


def normalize_hashtag(tag: str) -> str:
    """
    Normaliza una categoría al formato canónico:
    - Siempre empieza por #
    - Solo conserva [a-zA-Z0-9_]
    - Primera letra en mayúscula
    """
    raw = (tag or "").strip()
    if not raw:
        return ""

    if raw.startswith("#"):
        raw = raw[1:]

    normalized = "".join(ch for ch in raw if ch.isalnum() or ch == "_")
    if not normalized:
        return ""

    normalized = normalized[0].upper() + normalized[1:]
    return f"#{normalized}"


def is_valid_hashtag(tag: str) -> bool:
    normalized = normalize_hashtag(tag)
    if not normalized:
        return False
    return bool(HASHTAG_PATTERN.fullmatch(normalized))


def extract_hashtags(text: str) -> Set[str]:
    if not text:
        return set()

    tags = set()
    for match in HASHTAG_PATTERN.findall(text):
        normalized = normalize_hashtag(match)
        if normalized:
            tags.add(normalized)
    return tags
