from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

import Levenshtein
import numpy as np
from scipy.sparse import csr_matrix

from text_scrubber.geo.overlap_c import get_overlap

# Global Levenshtein map for storing {char: char ID} to optimize Levenshtein distance
_LEVENSHTEIN_MAP = {}

# Bounds for Levenshtein distance
_LEVENSHTEIN_OVERLAP_BOUNDS = dict()
_LEVENSHTEIN_SIZE_BOUNDS = dict()


def find_closest_string_levenshtein(
        query: str,
        candidates: Dict[int, Dict[str, Union[csr_matrix, List[str], List[Tuple[int, int]]]]],
        min_score: float
) -> Optional[Tuple[List[Tuple[int, int]], float]]:
    """
    Find the closest match for a query string from a list of candidates using Levenshtein edit distance

    :param query: string to search for
    :param candidates: {size: {'levenshtein_tokens': List of cleaned locations (str),
                               'char_matrix': character occurrence matrix (csr_matrix),
                               'indices': List of corresponding indices (Tuple[int, int]}},
    :param min_score: minimum similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: (best candidates, score) when minimum score is obtained, None otherwise
    """
    # Obtain bounds. Note that the upper bound can be large or even infinite (when min_score==0.0). For those cases we
    # set it to the max size that occurs in the candidates
    (size_lower_bound, size_upper_bound), overlap_lower_bounds = find_levenshtein_bounds(len(query), min_score)
    size_upper_bound = min(size_upper_bound, max(candidates.keys(), default=-1) + 1)

    # Convert query to char tokens
    query_tokens = get_char_tokens(query)

    # Obtain scores and determine best option taking into account the minimum score threshold
    overall_best_candidates = []
    overall_best_score = min_score
    for size in range(size_lower_bound, size_upper_bound):

        if size not in candidates:
            continue

        levenshtein_tokens = candidates[size]['levenshtein_tokens']
        char_matrix = candidates[size]['char_matrix']
        indices = candidates[size]['indices']

        # Obtain overlap and use lower bound
        char_overlap = get_char_overlap(query_tokens, char_matrix)
        overlap_lower_bound = overlap_lower_bounds[size]
        above_threshold = np.where(char_overlap >= overlap_lower_bound)[0]

        for idx in above_threshold:
            score = Levenshtein.ratio(query, levenshtein_tokens[idx])
            if score >= overall_best_score:
                if score == overall_best_score:
                    overall_best_candidates.append(indices[idx])
                else:
                    overall_best_candidates = [indices[idx]]
                    overall_best_score = score

    if overall_best_candidates:
        return overall_best_candidates, overall_best_score


def get_char_overlap(query_tokens: List[int], char_matrix: csr_matrix) -> np.ndarray:
    """
    The char_matrix contains the different candidates in the rows, and character occurrences in the columns. We take the
    sum over the minimum values at each column of the matrix with the query vector, which yields the number of
    overlapping characters.

    :param query_tokens: list of char tokens
    :param char_matrix: the char_matrix contains the different candidates in the rows, and characters in the columns.
        If a character occurs in a candidate than that value is incremented
    :return: vector containing number of overlapping characters
    """
    query_vector = np.zeros(char_matrix.shape[1], dtype=np.int32)
    for token in query_tokens:
        if token < len(query_vector):
            query_vector[token] += 1

    return get_overlap(query_vector, char_matrix.data, char_matrix.indptr, char_matrix.indices)


def get_char_tokens(query: str) -> List[int]:
    """
    Obtain a list of char tokens from a string.
    E.g., 'hello world' --> ['h', 'e', 'l', 'l', 'o', ' ', 'w', 'o', 'r', 'l', 'd'].

    The characters are converted to integers, to save precious memory and to make the matching process quicker.

    :param query: string to extract char tokens from
    :return: list of char tokens
    """
    global _LEVENSHTEIN_MAP
    query_tokens = [_LEVENSHTEIN_MAP.setdefault(ch, len(_LEVENSHTEIN_MAP)) for ch in query]

    return query_tokens


def optimize_levenshtein_strings(strings: List[str]) -> csr_matrix:
    """
    Optimize data structure for trigrams. It transforms a list of candidates, where each candidate is represented as a
    set of integers, to a single csr_matrix.

    :param strings: list of strings
    :return: compressed sparse matrix that stores the number of character occurrences
    """
    # Convert strings to a list of integers
    string_tokens = (sorted(get_char_tokens(string)) for string in strings)

    # Convert to sparse matrix format
    data, row_ind, col_ind = [], [], []
    for row_idx, sorted_tokens in enumerate(string_tokens):
        prev_token = -1
        for token in sorted_tokens:
            if token != prev_token:
                data.append(1)
                row_ind.append(row_idx)
                col_ind.append(token)
                prev_token = token
            else:
                data[-1] += 1

    char_matrix = csr_matrix((data, (row_ind, col_ind)))
    char_matrix.data = char_matrix.data.astype(np.int32)
    return char_matrix


def find_levenshtein_bounds(query_size: int, min_score: float) -> Tuple[Tuple[int, int], Dict[int, int]]:
    """
    Finds a lower and upper bound for a given query. If a candidate falls behind these bounds, it is guaranteed that the
    minimum score will never be reached. If the bounds are not known yet it will determine them on the fly.

    :param query_size: the query size
    :param min_score: minimum similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: (lower (inclusive) and upper (exclusive) bound) tuple and a
        {candidate size: lower bound (inclusive)} dictionary
    """
    global _LEVENSHTEIN_SIZE_BOUNDS, _LEVENSHTEIN_OVERLAP_BOUNDS

    if min_score not in _LEVENSHTEIN_SIZE_BOUNDS:
        _LEVENSHTEIN_SIZE_BOUNDS[min_score] = dict()
        _LEVENSHTEIN_OVERLAP_BOUNDS[min_score] = dict()

    if query_size not in _LEVENSHTEIN_SIZE_BOUNDS[min_score]:
        # When min_score equals 0.0 this will loop on forever, so we treat this special case differently
        if min_score == 0.0:
            lower_bound = -1
            upper_bound = np.inf

        # Determine for the string size bounds
        else:
            query = 'a' * query_size
            lower_bound = upper_bound = query_size
            while lower_bound >= 0 and Levenshtein.ratio(query, query[:lower_bound]) >= min_score:
                lower_bound -= 1
            while Levenshtein.ratio(query, query + 'a' * (upper_bound - query_size)) >= min_score:
                upper_bound += 1

        _LEVENSHTEIN_SIZE_BOUNDS[min_score][query_size] = lower_bound + 1, upper_bound

        # Again, when min_score == 0.0 we will store infinite amounts of lower bounds, while we know all lower bounds
        # will be 0.0
        if min_score == 0.0:
            _LEVENSHTEIN_OVERLAP_BOUNDS[min_score][query_size] = defaultdict(int)

        # Determine for the overlap bounds
        else:
            _LEVENSHTEIN_OVERLAP_BOUNDS[min_score][query_size] = dict()
            for candidate_size in range(lower_bound + 1, upper_bound):
                lower_bound = candidate_size
                query = 'a' * query_size
                while lower_bound >= 0 and \
                        Levenshtein.ratio(query, 'b' * (candidate_size - lower_bound) + 'a' * lower_bound) >= min_score:
                    lower_bound -= 1
                _LEVENSHTEIN_OVERLAP_BOUNDS[min_score][query_size][candidate_size] = lower_bound + 1

    return _LEVENSHTEIN_SIZE_BOUNDS[min_score][query_size], _LEVENSHTEIN_OVERLAP_BOUNDS[min_score][query_size]
