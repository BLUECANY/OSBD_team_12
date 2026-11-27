import unittest

from ocr.product_info import extract_product_info


class ProductInfoTests(unittest.TestCase):
    def test_actual_side_photo_does_not_invent_product(self):
        result = extract_product_info({
            "rec_texts": ["んやり", "EIB3E", "良感ウェ~プ!", "りも", "もCE心氧思", "7ミ", "グレープ味"],
            "rec_scores": [0.6551286578, 0.4391582608, 0.7369459867, 0.966478765,
                           0.3485133648, 0.5540060401, 0.975769043],
        })
        self.assertIsNone(result["brand_candidate"])
        self.assertIsNone(result["search_query"])
        self.assertTrue(result["needs_confirmation"])
        self.assertIn("グレープ味", result["variant_candidates"])
        self.assertNotIn("しゃりもにグミ", str(result))

    def test_clean_synthetic_example_still_requires_review(self):
        result = extract_product_info({"rec_texts": ["BOURBON", "しゃりもにグミ", "グレープ味", "内容量 50g"],
                                       "rec_scores": [0.96] * 4})
        self.assertEqual(result["brand_candidate"], "BOURBON")
        self.assertEqual(result["product_name_candidate"], "しゃりもにグミ")
        self.assertIn("50g", result["volume_candidates"])
        self.assertEqual(result["query_candidates"][0], "BOURBON しゃりもにグミ")
        self.assertTrue(result["needs_confirmation"])

    def test_empty_and_mismatched_data(self):
        self.assertIsNone(extract_product_info({"rec_texts": [], "rec_scores": []})["search_query"])
        with self.assertRaises(ValueError):
            extract_product_info({"rec_texts": ["hello"], "rec_scores": []})

    def test_low_confidence_and_nutrition_are_not_size_evidence(self):
        result = extract_product_info({"rec_texts": ["protein 5g", "250ml", "BOURBON"],
                                       "rec_scores": [0.99, 0.2, 0.3]})
        self.assertEqual(result["volume_candidates"], [])
        self.assertEqual(result["brand_candidates"], [])

    def test_alias_boundary_and_ambiguous_brands(self):
        result = extract_product_info({"rec_texts": ["BOURBONATE"], "rec_scores": [0.99]})
        self.assertIsNone(result["brand_candidate"])
        result = extract_product_info({"rec_texts": ["BOURBON", "SENKA"], "rec_scores": [0.99, 0.99]})
        self.assertIsNone(result["brand_candidate"])
        self.assertEqual(len(result["brand_candidates"]), 2)

    def test_fullwidth_units_and_wrapped_json(self):
        result = extract_product_info({"res": {"rec_texts": ["内容量 ５０ｍＬ"], "rec_scores": [0.9]}})
        self.assertEqual(result["volume_candidates"], ["50ml"])

    def test_only_human_confirmation_releases_query(self):
        result = extract_product_info({"rec_texts": [], "rec_scores": []},
                                      confirmed_product_name="  BOURBON  しゃりもにグミ ")
        self.assertEqual(result["search_query"], "BOURBON しゃりもにグミ")
        self.assertFalse(result["needs_confirmation"])
        with self.assertRaises(ValueError):
            extract_product_info({}, confirmed_product_name=" ")

    def test_invalid_score_rejected(self):
        for score in (float("nan"), 1.2, -0.1):
            with self.assertRaises(ValueError):
                extract_product_info({"rec_texts": ["text"], "rec_scores": [score]})


if __name__ == "__main__":
    unittest.main()
