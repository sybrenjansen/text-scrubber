import unittest
from collections import defaultdict
from unittest.mock import patch

import numpy as np

from text_scrubber.geo.string_distance_levenshtein import (get_char_overlap, get_char_tokens,
                                                           find_closest_string_levenshtein, find_levenshtein_bounds,
                                                           optimize_levenshtein_strings)

MODULE_NAME = 'text_scrubber.geo.string_distance_levenshtein'


class FindClosestStringLevenshteinTest(unittest.TestCase):

    def test_perfect_match(self):
        """
        Perfect matches should return score 1.0
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            candidates = self._create_data()
            matches, match_score = find_closest_string_levenshtein("hello", candidates, min_score=0.8)
            self.assertListEqual(matches, [0])
            self.assertEqual(match_score, 1.0)

            matches, match_score = find_closest_string_levenshtein("world", candidates, min_score=1.0)
            self.assertListEqual(matches, [1])
            self.assertEqual(match_score, 1.0)

    def test_close_matches(self):
        """
        Close matches should return when their score is above the threshold
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            candidates = self._create_data()
            matches, match_score = find_closest_string_levenshtein("helo", candidates, min_score=0.8)
            self.assertListEqual(matches, [0])
            self.assertAlmostEqual(match_score, 0.889, places=3)

            matches, match_score = find_closest_string_levenshtein("woord", candidates, min_score=0.8)
            self.assertListEqual(matches, [1])
            self.assertAlmostEqual(match_score, 0.8, places=3)

    def test_not_exceeding_threshold(self):
        """
        Close matches should return when their score is above the threshold
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            candidates = self._create_data()
            matches = find_closest_string_levenshtein("helo", candidates, min_score=0.9)
            self.assertIsNone(matches)

            matches = find_closest_string_levenshtein("woord", candidates, min_score=0.9)
            self.assertIsNone(matches)

    def test_multiple_matches(self):
        """
        When there are multiple matches, it should return the best only. When scores are tied multiple can be returned
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            candidates = self._create_data()
            matches, match_score = find_closest_string_levenshtein("helo", candidates, min_score=0.0)
            self.assertListEqual(matches, [0])
            self.assertAlmostEqual(match_score, 0.889, places=3)

            matches, match_score = find_closest_string_levenshtein("woord", candidates, min_score=0.0)
            self.assertListEqual(matches, [1])
            self.assertAlmostEqual(match_score, 0.8, places=3)

            matches, match_score = find_closest_string_levenshtein("l", candidates, min_score=0.0)
            self.assertListEqual(matches, [0, 1])
            self.assertAlmostEqual(match_score, 0.333, places=3)

    def test_no_candidates(self):
        """
        When there are candidates, it should return None
        """
        matches = find_closest_string_levenshtein("hello", {}, min_score=0.0)
        self.assertIsNone(matches)

    @staticmethod
    def _create_data():
        """
        Normally, we would use setup method for this, but we need the patch
        """
        char_matrix = optimize_levenshtein_strings(["hello", "world"])
        candidates = {5: {'levenshtein_tokens': ["hello", "world"],
                          'char_matrix': char_matrix,
                          'indices': [0, 1]}}
        return candidates


class GetCharOverlapTest(unittest.TestCase):

    def test_out_of_bounds_tokens(self):
        """
        The char_matrix does not contain the character 'b', so that one should not be encoded in the query vector.
        The character to index mapping is: {'h': 0, 'e': 1, 'l': 2, 'o': 3, ' ': 4, 'w': 5, 'r': 6, 'd': 7}
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            char_matrix = optimize_levenshtein_strings(["hello ", "world"])
            with patch(f'{MODULE_NAME}.get_overlap') as p:
                get_char_overlap(query_tokens=get_char_tokens("bed"), char_matrix=char_matrix)
                query_vector = p.call_args[0][0]
                self.assertListEqual(query_vector.tolist(), [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])

    def test_overlap(self):
        """
        Test that overlap between query and candidates is correctly calculated
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            char_matrix = optimize_levenshtein_strings(["hello ", "world"])

            with self.subTest('Single character overlap with both candidates'):
                n_overlap = get_char_overlap(query_tokens=get_char_tokens("bed"), char_matrix=char_matrix)
                self.assertEqual(n_overlap.tolist(), [1, 1])

            with self.subTest('Multiple character overlap'):
                n_overlap = get_char_overlap(query_tokens=get_char_tokens("held"), char_matrix=char_matrix)
                self.assertEqual(n_overlap.tolist(), [3, 2])
                n_overlap = get_char_overlap(query_tokens=get_char_tokens("hellllo"), char_matrix=char_matrix)
                self.assertEqual(n_overlap.tolist(), [5, 2])

            with self.subTest('No character overlap'):
                n_overlap = get_char_overlap(query_tokens=get_char_tokens("zzz"), char_matrix=char_matrix)
                self.assertEqual(n_overlap.tolist(), [0, 0])


class GetCharTokensTest(unittest.TestCase):

    def test_char_tokens(self):
        """
        Test that characters are correctly added to the Levenshtein map
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}) as LEVENSHTEIN_MAP:
            query_tokens = get_char_tokens("hello ")
            self.assertListEqual(query_tokens, [0, 1, 2, 2, 3, 4])
            self.assertDictEqual(LEVENSHTEIN_MAP, {'h': 0, 'e': 1, 'l': 2, 'o': 3, ' ': 4})

            query_tokens = get_char_tokens("world")
            self.assertListEqual(query_tokens, [5, 3, 6, 2, 7])
            self.assertDictEqual(LEVENSHTEIN_MAP, {'h': 0, 'e': 1, 'l': 2, 'o': 3, ' ': 4, 'w': 5, 'r': 6, 'd': 7})


class OptimizeLevenshteinStringsTest(unittest.TestCase):

    def test_char_matrix(self):
        """
        Check that the character matrix is correctly constructed. For the example below the character to index mapping
        looks like:
        _LEVENSHTEIN_MAP = {'h': 0, 'e': 1, 'l': 2, 'o': 3, ' ': 4, 'w': 5, 'r': 6, 'd': 7, 'a': 8, 'b': 9, 'c': 10}
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_MAP', new={}):
            char_matrix = optimize_levenshtein_strings(["hello ", "world"])
            self.assertListEqual(char_matrix.todense().tolist(), [[1, 1, 2, 1, 1, 0, 0, 0],
                                                                  [0, 0, 1, 1, 0, 1, 1, 1]])
            char_matrix = optimize_levenshtein_strings(["aaa", "bb", "cccc", "ddddd"])
            self.assertListEqual(char_matrix.todense().tolist(), [[0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
                                                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
                                                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
                                                                  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0]])


class FindLevenshteinBoundsTest(unittest.TestCase):

    def test_size_bounds(self):
        """
        Test bounds. Note that lower bound is included and upper bound is excluded from the range.
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_SIZE_BOUNDS', new=dict()) as size_bounds, \
                patch(f'{MODULE_NAME}._LEVENSHTEIN_OVERLAP_BOUNDS', new=dict()):
            find_levenshtein_bounds(1, min_score=0.5)
            self.assertDictEqual(size_bounds, {0.5: {1: (1, 4)}})
            find_levenshtein_bounds(2, min_score=0.5)
            find_levenshtein_bounds(10, min_score=0.5)
            self.assertDictEqual(size_bounds, {0.5: {1: (1, 4),
                                                     2: (1, 7),
                                                     10: (4, 31)}})

            find_levenshtein_bounds(1, min_score=0.25)
            find_levenshtein_bounds(3, min_score=0.25)
            find_levenshtein_bounds(17, min_score=0.25)
            find_levenshtein_bounds(20, min_score=0.0)
            self.assertDictEqual(size_bounds, {0.5: {1: (1, 4),
                                                     2: (1, 7),
                                                     10: (4, 31)},
                                               0.25: {1: (1, 8),
                                                      3: (1, 22),
                                                      17: (3, 120)},
                                               0.0: {20: (0, np.inf)}})

    def test_overlap_bounds(self):
        """
        Check that for each threshold-query size combination there is an entry. For each combination the entries should
        reflect the lower and upper bounds
        """
        with patch(f'{MODULE_NAME}._LEVENSHTEIN_SIZE_BOUNDS', new=dict()), \
                patch(f'{MODULE_NAME}._LEVENSHTEIN_OVERLAP_BOUNDS', new=dict()) as overlap_bounds:
            find_levenshtein_bounds(1, min_score=0.5)
            self.assertDictEqual(overlap_bounds,
                                 {0.5: {1: {1: 1, 2: 1, 3: 1}}})
            find_levenshtein_bounds(2, min_score=0.5)
            find_levenshtein_bounds(4, min_score=0.5)
            self.assertDictEqual(overlap_bounds,
                                 {0.5: {1: {1: 1, 2: 1, 3: 1},
                                        2: {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2},
                                        4: {2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3, 9: 4, 10: 4, 11: 4, 12: 4}}})

            find_levenshtein_bounds(1, min_score=0.8)
            find_levenshtein_bounds(3, min_score=0.8)
            find_levenshtein_bounds(9, min_score=0.8)
            self.assertEqual(overlap_bounds,
                             {0.5: {1: {1: 1, 2: 1, 3: 1},
                                    2: {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2},
                                    4: {2: 2, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3, 9: 4, 10: 4, 11: 4, 12: 4}},
                              0.8: {1: {1: 1},
                                    3: {2: 2, 3: 3, 4: 3},
                                    9: {6: 6, 7: 7, 8: 7, 9: 8, 10: 8, 11: 8, 12: 9, 13: 9}}})

            # When min_score == 0.0 it stores the lower bound in a defaultdict, as it will always be 0.0
            find_levenshtein_bounds(20, min_score=0.0)
            self.assertIsInstance(overlap_bounds[0.0][20], defaultdict)
            self.assertTrue(all(overlap_bounds[0.0][20][size] == 0.0) for size in [0, 1, 1336, 123456789])
