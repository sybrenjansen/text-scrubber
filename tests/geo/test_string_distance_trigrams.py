import unittest
from unittest.mock import patch

import numpy as np

from text_scrubber.geo.string_distance_trigrams import (get_trigram_tokens, find_closest_string_trigrams,
                                                        find_trigram_bounds, optimize_trigram_tokens,
                                                        trigram_similarity, trigram_similarity_naive)

MODULE_NAME = 'text_scrubber.geo.string_distance_trigrams'


class FindClosestStringTrigramsTest(unittest.TestCase):

    def test_perfect_match(self):
        """
        Perfect matches should return score 1.0
        """
        with patch(f'{MODULE_NAME}._TRIGRAM_MAP', new={}):
            candidates = self._create_data()
            matches, match_score = find_closest_string_trigrams("hello", candidates, min_score=0.8)
            self.assertListEqual(matches, [0])
            self.assertEqual(match_score, 1.0)

            matches, match_score = find_closest_string_trigrams("world", candidates, min_score=1.0)
            self.assertListEqual(matches, [1])
            self.assertEqual(match_score, 1.0)

    def test_close_matches(self):
        """
        Close matches should return when their score is above the threshold
        """
        with patch(f'{MODULE_NAME}._TRIGRAM_MAP', new={}):
            candidates = self._create_data()
            matches, match_score = find_closest_string_trigrams("helo", candidates, min_score=0.2)
            self.assertListEqual(matches, [0])
            self.assertAlmostEqual(match_score, 0.625, places=3)

            matches, match_score = find_closest_string_trigrams("woord", candidates, min_score=0.2)
            self.assertListEqual(matches, [1])
            self.assertAlmostEqual(match_score, 0.273, places=3)

    def test_not_exceeding_threshold(self):
        """
        Close matches should return when their score is above the threshold
        """
        with patch(f'{MODULE_NAME}._TRIGRAM_MAP', new={}):
            candidates = self._create_data()
            matches = find_closest_string_trigrams("helo", candidates, min_score=0.9)
            self.assertIsNone(matches)

            matches = find_closest_string_trigrams("woord", candidates, min_score=0.9)
            self.assertIsNone(matches)

    def test_multiple_matches(self):
        """
        When there are multiple matches, it should return the best only. When scores are tied multiple can be returned
        """
        with patch(f'{MODULE_NAME}._TRIGRAM_MAP', new={}):
            candidates = self._create_data()
            matches, match_score = find_closest_string_trigrams("helo", candidates, min_score=0.0)
            self.assertListEqual(matches, [0])
            self.assertAlmostEqual(match_score, 0.625, places=3)

            matches, match_score = find_closest_string_trigrams("woord", candidates, min_score=0.0)
            self.assertListEqual(matches, [1])
            self.assertAlmostEqual(match_score, 0.273, places=3)

            matches, match_score = find_closest_string_trigrams("h d", candidates, min_score=0.0)
            self.assertListEqual(matches, [0, 1])
            self.assertAlmostEqual(match_score, 0.083, places=3)

    def test_no_candidates(self):
        """
        When there are candidates, it should return None
        """
        matches = find_closest_string_trigrams("hello", {}, min_score=0.0)
        self.assertIsNone(matches)

    @staticmethod
    def _create_data():
        """
        Normally, we would use setup method for this, but we need the patch
        """
        candidate_trigram_tokens = [get_trigram_tokens("hello"), get_trigram_tokens("world")]
        trigram_matrix = optimize_trigram_tokens(candidate_trigram_tokens)
        candidates = {len(candidate_trigram_tokens[0]): {'trigram_tokens': trigram_matrix,
                                                         'indices': [0, 1]}}
        return candidates


class TrigramSimilarityTest(unittest.TestCase):

    def test_out_of_bounds_tokens(self):
        """
        The trigram_matrix does not contain the trigrams 7 and 8, so those should not be encoded in the query vector
        """
        trigram_matrix = optimize_trigram_tokens([{0, 1, 3}, {1, 4, 6}])
        with patch.object(trigram_matrix, 'dot', side_effect=trigram_matrix.dot) as p:
            trigram_similarity(query_trigram_tokens={0, 1, 7, 8}, candidates_n_tokens=3, trigram_matrix=trigram_matrix)
            query_vector = p.call_args[0][0]
            self.assertListEqual(query_vector.tolist(), [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_overlap(self):
        """
        Test that overlap between query and candidates is correctly calculated
        """
        trigram_matrix = optimize_trigram_tokens([{0, 1, 3}, {1, 4, 6}])

        # Perfect/partial matches
        self.assertEqual(trigram_similarity({0, 1, 3}, 3, trigram_matrix).tolist(), [1.0, 0.2])
        self.assertEqual(trigram_similarity({1, 4, 6}, 3, trigram_matrix).tolist(), [0.2, 1.0])

        # Partial matches
        self.assertAlmostEqual(trigram_similarity({0, 3}, 3, trigram_matrix)[0], 0.667, places=3)
        self.assertEqual(trigram_similarity({0, 3}, 3, trigram_matrix)[1], 0.0)
        self.assertEqual(trigram_similarity({0, 4, 6}, 3, trigram_matrix).tolist(), [0.2, 0.5])

        # No match
        self.assertEqual(trigram_similarity({2, 5, 7, 8, 9, 10}, 3, trigram_matrix).tolist(), [0.0, 0.0])
        self.assertEqual(trigram_similarity(set(), 3, trigram_matrix).tolist(), [0.0, 0.0])

        # Altering candidates_n_tokens. Normally, they correspond to the size of the candidates, so changing it here
        # doesn't make any sense
        self.assertAlmostEqual(trigram_similarity({0, 4, 6}, 1, trigram_matrix)[0], 0.333, places=3)
        self.assertAlmostEqual(trigram_similarity({0, 4, 6}, 1, trigram_matrix)[1], 1.0, places=3)
        self.assertAlmostEqual(trigram_similarity({0, 4, 6}, 5, trigram_matrix)[0], 0.143, places=3)
        self.assertAlmostEqual(trigram_similarity({0, 4, 6}, 5, trigram_matrix)[1], 0.333, places=3)


class TrigramSimilarityNaiveTest(unittest.TestCase):

    def test_perfect_match(self):
        """
        Perfect matches should yield a score of 1.0
        """
        self.assertEqual(trigram_similarity_naive({0, 1, 2}, {0, 2, 1}), 1.0)
        self.assertEqual(trigram_similarity_naive({3}, {3}), 1.0)
        self.assertEqual(trigram_similarity_naive(set(), set()), 1.0)

    def test_partial_match(self):
        """
        Partial matches should yield a score > 0 and < 1
        """
        self.assertEqual(trigram_similarity_naive({0, 1, 2}, {0, 2, 1, 3}), 0.75)
        self.assertEqual(trigram_similarity_naive({3, 4}, {4}), 0.5)
        self.assertAlmostEqual(trigram_similarity_naive({0, 1, 2, 3, 4, 5}, {1}), 0.167, places=3)

    def test_no_match(self):
        """
        When there's no overlap, it should yield a score of 0.0
        """
        self.assertEqual(trigram_similarity_naive({0, 1, 2}, {3, 5}), 0.0)
        self.assertEqual(trigram_similarity_naive({0, 1, 2}, set()), 0.0)
        self.assertEqual(trigram_similarity_naive(set(), {3, 5}), 0.0)


class GetTrigramTokensTest(unittest.TestCase):

    def test_get_trigram_tokens(self):
        """
        Test that trigrams are correctly added to the trigrams map
        """
        with patch(f'{MODULE_NAME}._TRIGRAM_MAP', new={}) as TRIGRAM_MAP:
            query_tokens = get_trigram_tokens("hello")
            self.assertSetEqual(query_tokens, {0, 1, 2, 3, 4, 5, 6})
            self.assertDictEqual(TRIGRAM_MAP, {'  h': 0, ' he': 1, 'hel': 2, 'ell': 3, 'llo': 4, 'lo ': 5, 'o  ': 6})

            query_tokens = get_trigram_tokens("world")
            self.assertSetEqual(query_tokens, {7, 8, 9, 10, 11, 12, 13})
            self.assertDictEqual(TRIGRAM_MAP,
                                 {'  h': 0, ' he': 1, 'hel': 2, 'ell': 3, 'llo': 4, 'lo ': 5, 'o  ': 6,
                                  '  w': 7, ' wo': 8, 'wor': 9, 'orl': 10, 'rld': 11, 'ld ': 12, 'd  ': 13})

            # Mapping is not updated as all trigrams already exist
            query_tokens = get_trigram_tokens("hello world")
            self.assertSetEqual(query_tokens, {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13})
            self.assertDictEqual(TRIGRAM_MAP,
                                 {'  h': 0, ' he': 1, 'hel': 2, 'ell': 3, 'llo': 4, 'lo ': 5, 'o  ': 6,
                                  '  w': 7, ' wo': 8, 'wor': 9, 'orl': 10, 'rld': 11, 'ld ': 12, 'd  ': 13})


class OptimizeTrigramTokensTest(unittest.TestCase):

    def test_trigram_matrix(self):
        """
        Check that the trigram matrix is correctly constructed
        """
        trigram_matrix = optimize_trigram_tokens([{0, 1, 3}, {1, 4, 6}])
        self.assertListEqual(trigram_matrix.todense().tolist(), [[1, 1, 0, 1, 0, 0, 0],
                                                                 [0, 1, 0, 0, 1, 0, 1]])
        trigram_matrix = optimize_trigram_tokens([{0}, {1}, {1, 3}, {4}])
        self.assertListEqual(trigram_matrix.todense().tolist(), [[1, 0, 0, 0, 0],
                                                                 [0, 1, 0, 0, 0],
                                                                 [0, 1, 0, 1, 0],
                                                                 [0, 0, 0, 0, 1]])


class FindTrigramBoundsTest(unittest.TestCase):

    def test_size_bounds(self):
        """
        Test bounds. Note that lower bound is included and upper bound is excluded from the range.
        """
        with patch(f'{MODULE_NAME}._TRIGRAM_SIZE_BOUNDS', new=dict()) as size_bounds:
            find_trigram_bounds(1, min_score=0.5)
            self.assertDictEqual(size_bounds, {0.5: {1: (1, 3)}})
            find_trigram_bounds(2, min_score=0.5)
            find_trigram_bounds(10, min_score=0.5)
            self.assertDictEqual(size_bounds, {0.5: {1: (1, 3),
                                                     2: (1, 5),
                                                     10: (5, 21)}})

            find_trigram_bounds(1, min_score=0.25)
            find_trigram_bounds(3, min_score=0.25)
            find_trigram_bounds(17, min_score=0.25)
            find_trigram_bounds(20, min_score=0.0)
            self.assertDictEqual(size_bounds, {0.5: {1: (1, 3),
                                                     2: (1, 5),
                                                     10: (5, 21)},
                                               0.25: {1: (1, 5),
                                                      3: (1, 13),
                                                      17: (5, 69)},
                                               0.0: {20: (0, np.inf)}})
