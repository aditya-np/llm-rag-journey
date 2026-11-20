"""Text cleaning utilities. Goal: remove noise, preserve meaning and structure."""
import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return normalize_whitespace(text)
