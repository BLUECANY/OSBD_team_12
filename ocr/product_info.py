"""Conservative OCR-to-search preparation; no model or network dependency.

Candidates are suggestions, never verified product identities. A query is released
only when the caller supplies a product name explicitly confirmed by the user.
"""
import math
import re
import unicodedata


DEFAULT_BRANDS = {
    "BOURBON": ("BOURBON", "ブルボン"),
    "ANESSA": ("ANESSA", "アネッサ"),
    "SENKA": ("SENKA", "専科"),
    "Hada Labo": ("Hada Labo", "肌ラボ"),
    "Biore": ("Biore", "ビオレ"),
}
_SIZE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(ml|mL|ML|kg|KG|g|G|l|L)(?![A-Za-z])")
_NUTRITION = re.compile(r"栄養|熱量|たんぱく|脂質|炭水化物|食塩|糖質|protein|nutrition|sodium|fat", re.I)
_SLOGAN = re.compile(r"食感|ビタミン|パウダー|イメージ|写真|illustration|vitamin|https?://|www\.", re.I)
_FLAVOR = re.compile(r"([ぁ-んァ-ヶー一-龯]+味)")


def _clean(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _alias_in(text, alias):
    if alias.isascii():
        return re.search(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", text, re.I) is not None
    return alias in text


def extract_product_info(ocr_result, *, brand_aliases=None, min_score=0.7,
                         confirmed_product_name=None):
    """Accept reader.read_text output or PaddleOCR JSON (including res wrapper).

    min_score only filters within this OCR engine; it is not accuracy.
    confirmed_product_name must come from explicit human confirmation. Do not
    populate it automatically from product_name_candidate.
    """
    if not isinstance(ocr_result, dict):
        raise TypeError("ocr_result must be a dictionary")
    data = ocr_result.get("res", ocr_result)
    texts, scores = data.get("rec_texts", []), data.get("rec_scores", [])
    if len(texts) != len(scores):
        raise ValueError("rec_texts and rec_scores must have equal length")
    if not 0 <= min_score <= 1:
        raise ValueError("min_score must be between 0 and 1")
    brands = DEFAULT_BRANDS if brand_aliases is None else brand_aliases
    rows, brand_hits, sizes, flavors, candidates = [], [], [], [], []
    for original, score in zip(texts, scores):
        if not isinstance(original, str):
            raise TypeError("Each OCR text must be a string")
        score = float(score)
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Each OCR score must be finite and between 0 and 1")
        text = _clean(original)
        row = {"text": text, "score": score}
        rows.append(row)
        if not text or score < min_score:
            continue
        hits = [name for name, aliases in brands.items()
                if any(_alias_in(text, _clean(alias)) for alias in aliases)]
        for name in hits:
            if name not in brand_hits:
                brand_hits.append(name)
        flavor_matches = _FLAVOR.findall(text)
        for flavor in flavor_matches:
            if flavor not in flavors:
                flavors.append(flavor)
        size_matches = [] if _NUTRITION.search(text) else list(_SIZE.finditer(text))
        for match in size_matches:
            value = match.group(1) + match.group(2).lower()
            if value not in sizes:
                sizes.append(value)
        # Exclude metadata and obvious slogans; this is a heuristic, not NER.
        content = _SIZE.sub("", text)
        for flavor in flavor_matches:
            content = content.replace(flavor, "")
        for name in hits:
            for alias in brands[name]:
                content = re.sub(re.escape(_clean(alias)), "", content, flags=re.I)
        content = content.strip(" \t-:：!！、。()[]")
        letter_count = sum(ch.isalpha() for ch in content)
        if (letter_count >= 4 and not _SLOGAN.search(text)
                and not _NUTRITION.search(text) and not content.isnumeric()):
            if not any(c["text"] == content for c in candidates):
                candidates.append({"text": content, "score": score, "source_text": text})
    # Preserve OCR order. A high score does not prove a string is a product name.
    brand = brand_hits[0] if len(brand_hits) == 1 else None
    candidate = candidates[0]["text"] if candidates else None
    confirmed = None
    if confirmed_product_name is not None:
        if not isinstance(confirmed_product_name, str):
            raise TypeError("confirmed_product_name must be a string")
        confirmed = _clean(confirmed_product_name)
        if not confirmed:
            raise ValueError("Confirmed product name cannot be empty")
    suggestions = []
    for item in candidates:
        query = " ".join(part for part in (brand, item["text"]) if part)
        if query not in suggestions:
            suggestions.append(query)
    return {
        "brand_candidate": brand,
        "brand_candidates": brand_hits,
        "product_name_candidate": candidate,
        "product_candidates": candidates,
        "variant_candidates": flavors,
        "volume_candidates": sizes,
        "query_candidates": suggestions,
        "confirmed_product_name": confirmed,
        "search_query": confirmed,
        "needs_confirmation": confirmed is None,
        "reason": ("user_confirmed" if confirmed else
                   "review_candidates" if candidates else "no_reliable_product_candidate"),
        "ocr_lines": rows,
    }


def read_product_info(image_path, **options):
    """Optional integration with the existing OCR reader (lazy import)."""
    from .reader import read_text
    return extract_product_info(read_text(image_path), **options)
