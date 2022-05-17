import unittest
from unittest.mock import patch

from scipy.sparse import csr_matrix

from text_scrubber.geo.string_distance import find_closest_string


class FindClosestStringTest(unittest.TestCase):

    def setUp(self) -> None:
        # Content doesn't really matter, we will mock everything
        self.query = "aaaa"
        self.candidates = {'levenshtein': {4: {'levenshtein_tokens': ["aaab"],
                                               'char_matrix': csr_matrix((1, 1)),
                                               'indices': [0]}},
                           'trigrams': {4: {'trigram_tokens': csr_matrix((1, 1)),
                                            'indices': [1]}}}

    def test_thresholds(self):
        """
        Check if threshold are correctly passed on
        """
        for min_score_levenshtein, min_score_trigram in [(0.8, 0.5), (0.5, 0.8), (0.1, 0.1)]:
            with self.subTest(min_score_levenshtein=min_score_levenshtein, min_score_trigram=min_score_trigram), \
                    patch('text_scrubber.geo.string_distance.find_closest_string_levenshtein',
                          side_effect=lambda *_: None) as p_levenshtein, \
                    patch('text_scrubber.geo.string_distance.find_closest_string_trigrams',
                          side_effect=lambda *_: None) as p_trigrams:
                find_closest_string(self.query, self.candidates, min_score_levenshtein, min_score_trigram)
                self.assertEqual(p_levenshtein.call_args[0][-1], min_score_levenshtein)
                self.assertEqual(p_trigrams.call_args[0][-1], min_score_trigram)

    def test_trigram_similarity_is_called(self):
        """
        Check if trigram similarity is used when Levenshtein doesn't give results
        """
        with self.subTest('not called as levenshtein returns something'), \
                patch('text_scrubber.geo.string_distance.find_closest_string_levenshtein',
                      side_effect=lambda *_: "SOMETHING!") as p_levenshtein, \
                patch('text_scrubber.geo.string_distance.find_closest_string_trigrams',
                      side_effect=lambda *_: None) as p_trigrams:
            find_closest_string(self.query, self.candidates, 0.8, 0.5)
            self.assertEqual(p_levenshtein.call_count, 1)
            self.assertEqual(p_trigrams.call_count, 0)

        with self.subTest('called as levenshtein returns nothing'), \
                patch('text_scrubber.geo.string_distance.find_closest_string_levenshtein',
                      side_effect=lambda *_: None) as p_levenshtein, \
                patch('text_scrubber.geo.string_distance.find_closest_string_trigrams',
                      side_effect=lambda *_: None) as p_trigrams:
            find_closest_string(self.query, self.candidates, 0.8, 0.5)
            self.assertEqual(p_levenshtein.call_count, 1)
            self.assertEqual(p_trigrams.call_count, 1)
