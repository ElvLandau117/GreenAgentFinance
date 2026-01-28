import re


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    normalized = text.lower()
    normalized = normalized.replace(",", "")
    normalized = normalized.replace("$", " usd ")
    normalized = normalized.replace("%", " percent ")
    normalized = normalized.replace("bps", " basis points ")
    normalized = normalized.replace("bp", " basis points ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = normalized.replace("billion", " billion ")
    normalized = normalized.replace("million", " million ")
    normalized = normalized.replace("bn", " billion ")
    normalized = normalized.replace("mn", " million ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
