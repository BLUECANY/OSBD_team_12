import unittest
from unittest.mock import patch

from ocr.team_interface import (extract_product_info, extract_product_info_from_ocr,
                                inspect_ocr_result, apply_user_confirmation)


def ocr(*texts, score=0.95):
    return {"rec_texts": list(texts), "rec_scores": [score] * len(texts)}


class TeamInterfaceTests(unittest.TestCase):
    def test_exact_contract_and_path_forwarding(self):
        with patch("ocr.team_interface._read_image", return_value=ocr("BOURBON")) as reader:
            result = extract_product_info("example.jpg")
        reader.assert_called_once_with("example.jpg")
        self.assertEqual(set(result), {"brand", "product_name", "model", "price_text"})
        self.assertEqual(result["brand"], "BOURBON")
        self.assertIsNone(result["product_name"])

    def test_missing_image_error_is_not_swallowed(self):
        with patch("ocr.team_interface._read_image", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                extract_product_info("missing.jpg")

    def test_labels_and_price_original(self):
        result = extract_product_info_from_ocr(ocr("SENKA", "商品名：パーフェクトホイップ", "型番: AB-120", "税込 ￥５９８"))
        self.assertEqual(result, {"brand": "SENKA", "product_name": "パーフェクトホイップ",
                                  "model": "AB-120", "price_text": "税込 ￥５９８"})

    def test_does_not_promote_bad_candidate(self):
        result = inspect_ocr_result(ocr("BOURBON", "やりっと", "グレープ味"))
        self.assertIsNone(result["fields"]["product_name"])
        self.assertIn("やりっと", result["product_name_candidates"])
        self.assertTrue(result["needs_confirmation"])

    def test_actual_user_supplied_side_result(self):
        data = {"rec_texts": ["んやり", "EIB3E", "良感ウェ~プ!", "りも", "もCE心氧思", "7ミ", "グレープ味"],
                "rec_scores": [0.6551286578, 0.4391582608, 0.7369459867, 0.966478765,
                               0.3485133648, 0.5540060401, 0.975769043]}
        result = extract_product_info_from_ocr(data)
        self.assertTrue(all(value is None for value in result.values()))

    def test_multiple_prices_not_guessed(self):
        for lines in (("通常価格 ¥500", "特価 ¥398"), ("通常 ¥500 / 特価 ¥398",)):
            result = inspect_ocr_result(ocr(*lines))
            self.assertIsNone(result["fields"]["price_text"])
            self.assertIn("price_text", result["ambiguous_fields"])

    def test_no_price_from_quantity_or_number(self):
        result = extract_product_info_from_ocr(ocr("50g", "298", "賞味期限 2026.12.01", "10個"))
        self.assertIsNone(result["price_text"])
        self.assertIsNone(result["model"])

    def test_supported_price_formats(self):
        for text in ("JPY 298", "298円", "₩1,500", "1,500원", "$3.50", "EUR 4,99"):
            self.assertEqual(extract_product_info_from_ocr(ocr(text))["price_text"], text)

    def test_low_score_labels_not_used(self):
        result = extract_product_info_from_ocr(ocr("商品名: テスト商品", "型番: X1", "¥100", score=0.3))
        self.assertTrue(all(value is None for value in result.values()))

    def test_ambiguous_name_and_model(self):
        result = inspect_ocr_result(ocr("商品名: テスト商品", "商品名: 別の商品", "型番: X1", "型番: X2"))
        self.assertIsNone(result["fields"]["product_name"])
        self.assertIsNone(result["fields"]["model"])
        self.assertIn("product_name", result["ambiguous_fields"])

    def test_confirmed_name_and_price_clear_without_mutation(self):
        fields = extract_product_info_from_ocr(ocr("BOURBON", "¥500"))
        confirmed = apply_user_confirmation(fields, product_name="しゃりもにグミ グレープ味", price_text=None)
        self.assertEqual(confirmed["product_name"], "しゃりもにグミ グレープ味")
        self.assertIsNone(confirmed["price_text"])
        self.assertIsNone(fields["product_name"])
        self.assertEqual(fields["price_text"], "¥500")

    def test_invalid_confirmation_rejected(self):
        fields = extract_product_info_from_ocr(ocr())
        for values in ({"product_name": " "}, {"product_name": 123}, {"unknown": "x"}):
            with self.assertRaises((ValueError, TypeError)):
                apply_user_confirmation(fields, **values)

    def test_bad_schema_and_length(self):
        for data in ({}, {"res": None}, {"rec_texts": ["x"], "rec_scores": []}):
            with self.assertRaises((ValueError, TypeError)):
                extract_product_info_from_ocr(data)

    def test_wrapped_and_empty(self):
        self.assertEqual(extract_product_info_from_ocr({"res": ocr()}),
                         dict.fromkeys(("brand", "product_name", "model", "price_text")))

    def test_metadata_not_name_suggestion(self):
        result = inspect_ocr_result(ocr("JPY 298", "型番: ABCD-12", "内容量 150ml"))
        self.assertEqual(result["product_name_candidates"], [])


if __name__ == "__main__":
    unittest.main()
