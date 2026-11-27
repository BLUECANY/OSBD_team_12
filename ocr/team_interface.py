"""Team draft interface: image path -> brand/product_name/model/price_text.

Heuristic product-name suggestions are never promoted automatically. The basic
interface accepts explicit product-name labels; the UI can confirm other names.
Missing/ambiguous fields are None. OCR failures propagate to the caller.
"""
import re
import unicodedata

from .product_info import extract_product_info as _prepare_candidates

FIELDS = ("brand", "product_name", "model", "price_text")
_NAME = re.compile(r"^\s*(?:商品名|製品名|제품명|상품명|product\s*name)\s*[:：]\s*(.+?)\s*$", re.I)
_MODEL = re.compile(r"^\s*(?:型番|品番|モデル番号|모델명|모델번호|품번|model(?:\s*(?:no\.?|number))?)\s*[:：]\s*(.+?)\s*$", re.I)
_AMOUNT = r"\d+(?:[,.]\d+)*"
_CURRENCY = r"(?:JPY|KRW|USD|EUR|GBP)"
_PRICE = re.compile(
    rf"(?:[¥₩$€£]\s*{_AMOUNT}|\b{_CURRENCY}\s*{_AMOUNT}|"
    rf"{_AMOUNT}\s*(?:円|원|{_CURRENCY}\b))", re.I
)
_UNIT_ONLY = re.compile(r"\d+(?:[,.]\d+)?\s*(?:g|kg|mg|ml|l|個|개|枚|袋)", re.I)


def _normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _unique(values):
    return list(dict.fromkeys(values))


def _single(values):
    values = _unique(values)
    return values[0] if len(values) == 1 else None


def _validate_ocr(ocr_result):
    if not isinstance(ocr_result, dict):
        raise TypeError("OCR result must be a dictionary")
    data = ocr_result.get("res", ocr_result)
    if not isinstance(data, dict) or not {"rec_texts", "rec_scores"} <= data.keys():
        raise ValueError("OCR result needs rec_texts and rec_scores")
    if isinstance(data["rec_texts"], (str, bytes)) or isinstance(data["rec_scores"], (str, bytes)):
        raise TypeError("OCR fields must be sequences, not strings")
    return data


def inspect_ocr_result(ocr_result):
    """Detailed review payload for saved JSON or reader.read_text() output.

    Fields and candidates are derived solely from supplied text. The 0.7 score
    threshold is an initial heuristic, not an accuracy guarantee.
    """
    data = _validate_ocr(ocr_result)
    review = _prepare_candidates(data)
    names, models, prices, evidence = [], [], [], []
    for original, row in zip(data["rec_texts"], review["ocr_lines"]):
        if row["score"] < 0.7:
            continue
        text = row["text"]
        name_match, model_match = _NAME.fullmatch(text), _MODEL.fullmatch(text)
        if name_match:
            value = name_match.group(1).strip()
            if any(ch.isalpha() for ch in value) and not _UNIT_ONLY.fullmatch(value):
                names.append(value)
                evidence.append({"field": "product_name", "text": original, "score": row["score"]})
        if model_match:
            value = model_match.group(1).strip()
            if any(ch.isalnum() for ch in value):
                models.append(value)
                evidence.append({"field": "model", "text": original, "score": row["score"]})
        # Keep the original OCR line (including tax/discount context), not an
        # invented amount or converted currency. Multiple prices stay ambiguous.
        if not name_match and not model_match and _PRICE.search(text):
            prices.append(original.strip())
            evidence.append({"field": "price_text", "text": original, "score": row["score"]})
    price_lines = _unique(prices)
    price = price_lines[0] if len(price_lines) == 1 else None
    if price is not None and len(_PRICE.findall(_normalized(price))) != 1:
        price = None
    fields = {
        "brand": review["brand_candidate"],
        "product_name": _single(names),
        "model": _single(models),
        "price_text": price,
    }
    # Filter obvious labels/prices/metadata from legacy heuristic suggestions.
    name_candidates = []
    for item in review["product_candidates"]:
        source = item["source_text"]
        if (_NAME.fullmatch(source) or _MODEL.fullmatch(source)
                or _PRICE.search(source) or re.search(r"内容量|容量|重量|net\s*(?:weight|content)", source, re.I)):
            continue
        name_candidates.append(item["text"])
    name_candidates = _unique(names + name_candidates)
    return {
        "fields": fields,
        "product_name_candidates": name_candidates,
        "brand_candidates": review["brand_candidates"],
        "model_candidates": _unique(models),
        "price_candidates": price_lines,
        "variant_candidates": review["variant_candidates"],
        "volume_candidates": review["volume_candidates"],
        "needs_confirmation": True,
        "missing_fields": [key for key, value in fields.items() if value is None],
        "ambiguous_fields": [key for key, values in
                             (("brand", review["brand_candidates"]), ("product_name", _unique(names)),
                              ("model", _unique(models)), ("price_text", price_lines))
                             if len(values) > 1 or (key == "price_text" and values and price is None)],
        "evidence": evidence,
        "ocr_lines": review["ocr_lines"],
    }


def extract_product_info_from_ocr(ocr_result):
    """Four-field adapter for existing JSON; does not run OCR."""
    return inspect_ocr_result(ocr_result)["fields"]


def _read_image(image_path):
    # Imported lazily: the saved-JSON flow needs no PaddleOCR installation.
    from .reader import read_text
    return read_text(image_path)


def extract_product_info(image_path):
    """Team entry point. Returns exactly four keys, values are str or None."""
    return extract_product_info_from_ocr(_read_image(image_path))


def inspect_product_info(image_path):
    """UI entry point: fields, candidates and original text in one OCR run."""
    return inspect_ocr_result(_read_image(image_path))


def apply_user_confirmation(fields, **updates):
    """Apply explicit user edits; never call this as automatic OCR correction.

    Use the returned product_name with search_products(). Omitted fields stay
    unchanged; an empty string or None clears a field. Input is not mutated.
    """
    if not isinstance(fields, dict) or set(fields) != set(FIELDS):
        raise ValueError("Expected exactly brand, product_name, model, price_text")
    if set(updates) - set(FIELDS):
        raise ValueError("Unknown field in confirmation")
    result = dict(fields)
    for key, value in updates.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{key} must be a string or None")
        result[key] = _normalized(value) or None if value is not None else None
    for key, value in result.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{key} must be a string or None")
    if not result["product_name"] or not result["product_name"].strip():
        raise ValueError("A user-confirmed product name is required before search")
    return result
