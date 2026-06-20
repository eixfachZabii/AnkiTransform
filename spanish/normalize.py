"""Text normalization for duplicate detection."""
import re
import unicodedata

_PREFIX_RE = re.compile(r"^\d+\.\s*")
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize for comparison: strip Lektion prefix, NFC, lowercase, collapse whitespace."""
    text = _PREFIX_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    text = _WS_RE.sub(" ", text)
    return text
