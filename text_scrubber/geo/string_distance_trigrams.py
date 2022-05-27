from itertools import islice
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from scipy.sparse import csr_matrix

# Global trigram map for storing {trigram: trigram ID} to save memory
_TRIGRAM_MAP = {}

# Bounds for trigram distance
_TRIGRAM_SIZE_BOUNDS = dict()


def find_closest_string_trigrams(query: str, candidates: Dict[int, Dict[str, Union[csr_matrix, List[Tuple[int, int]]]]],
                                 min_score: float) -> Optional[Tuple[List[Tuple[int, int]], float]]:
    """
    Find the closest match for a string from a list of options using Levenshtein edit distance

    :param query: string to search for
    :param candidates: {size: {'trigram_tokens': trigram matrix (csr_matrix),
                               'indices': List of corresponding indices (Tuple[int, int])}}
    :param min_score: minimum similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: (best candidates, score) when minimum score is obtained, None otherwise
    """
    # Get trigram tokens for query string
    query_trigram_tokens = get_trigram_tokens(query)

    # Obtain bounds. Note that the upper bound can be large or even infinite (when min_score==0.0). For those cases we
    # set it to the max size that occurs in the candidates
    size_lower_bound, size_upper_bound = find_trigram_bounds(len(query_trigram_tokens), min_score)
    size_upper_bound = min(size_upper_bound, max(candidates.keys(), default=-1) + 1)

    # Obtain scores and determine best candidates taking into account the minimum score threshold
    overall_best_candidates = []
    overall_best_score = min_score
    for size in range(size_lower_bound, size_upper_bound):

        if size not in candidates:
            continue

        trigram_matrix = candidates[size]['trigram_tokens']
        indices = candidates[size]['indices']

        scores = trigram_similarity(query_trigram_tokens, size, trigram_matrix)

        # Determine best matches
        best_score = np.max(scores)
        if best_score >= overall_best_score:
            best_candidates = np.where(scores == best_score)[0]
            best_candidates = [indices[idx] for idx in best_candidates]
            if best_score == overall_best_score:
                overall_best_candidates.extend(best_candidates)
            else:
                overall_best_score = best_score
                overall_best_candidates = best_candidates

    if overall_best_candidates:
        return overall_best_candidates, overall_best_score


def trigram_similarity(query_trigram_tokens: Set[int], candidates_n_tokens: int,
                       trigram_matrix: csr_matrix) -> np.ndarray:
    """
    The trigram_matrix contains the different candidates in the rows, and trigrams in the columns. We take the dot
    product of the matrix with the query vector, which yields the number of overlapping trigrams. From there, we
    calculate the trigram similarities.

    :param query_trigram_tokens: set of trigrams belonging to the query string
    :param candidates_n_tokens: number of trigram tokens available in the candidates
    :param trigram_matrix: the trigram_matrix contains the different candidates in the rows, and trigrams in the
        columns. If a trigram occurs in a candidate than that value is set to 1
    :return: vector of scores
    """
    query_vector = np.zeros(trigram_matrix.shape[1])
    query_vector[[token for token in query_trigram_tokens if token < trigram_matrix.shape[1]]] = 1.0

    n_overlap = trigram_matrix.dot(query_vector)
    scores = n_overlap / (len(query_trigram_tokens) + candidates_n_tokens - n_overlap)

    return scores


def trigram_similarity_naive(string_trigrams: Set[int], option_trigrams: Set[int]) -> float:
    """
    Computes the trigram similarity

    :param string_trigrams: set of trigrams belonging to the search string
    :param option_trigrams: set of trigrams belonging to the option
    :return: trigram similarity
    """
    if len(string_trigrams) == len(option_trigrams) == 0:
        return 1.0
    n_overlap = len(string_trigrams & option_trigrams)
    return n_overlap / (len(string_trigrams) + len(option_trigrams) - n_overlap)


def get_trigram_tokens(string: str) -> Set[int]:
    """
    Obtain a set of trigram tokens from a string. E.g., 'hello world' --> {'  h', ' he', 'hel', 'ell', 'llo', 'lo ',
    'o  ', '  w', ' wo', 'wor', 'orl', 'rld', 'ld ', 'd  '}.

    The trigrams are converted to integers, to save precious memory and to make the matching process quicker.

    :param string: string to extract trigrams from
    :return: set of trigram integers
    """
    global _TRIGRAM_MAP
    string = f"  {string.replace(' ', '  ')}  "
    return {_TRIGRAM_MAP.setdefault(string[i:i + 3], len(_TRIGRAM_MAP)) for i in range(len(string) - 2)}


def optimize_trigram_tokens(trigrams: List[Set[int]]) -> csr_matrix:
    """
    Optimize data structure for trigrams. It transforms a list of candidates, where each candidate is represented as a
    set of integers, to a single csr_matrix.

    :param trigrams: list of trigram sets
    :return: binary compressed sparse matrix that stores trigram occurrences
    """
    row_ind, col_ind = [], []
    for row_idx, trigram_tokens in enumerate(trigrams):
        row_ind.extend([row_idx for _ in range(len(trigram_tokens))])
        col_ind.extend(trigram_tokens)
    trigram_matrix = csr_matrix(([1] * len(row_ind), (row_ind, col_ind)))
    trigram_matrix.data = trigram_matrix.data.astype(np.int32)
    return trigram_matrix


def find_trigram_bounds(query_size: int, min_score: float) -> Tuple[int, int]:
    """
    Finds a lower and upper bound for a given query. If a candidate falls behind these bounds, it is guaranteed that the
    minimum score will never be reached. If the bounds are not known yet it will determine them on the fly.

    :param query_size: the query size
    :param min_score: minimum trigram similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: lower (inclusive) and upper (exclusive) bound
    """
    global _TRIGRAM_SIZE_BOUNDS

    if min_score not in _TRIGRAM_SIZE_BOUNDS:
        _TRIGRAM_SIZE_BOUNDS[min_score] = dict()

    if query_size not in _TRIGRAM_SIZE_BOUNDS[min_score]:
        # When min_score equals 0.0 this will loop on forever, so we treat this special case differently
        if min_score == 0.0:
            lower_bound = -1
            upper_bound = np.inf

        # Determine bounds
        else:
            query = set(range(query_size))
            lower_bound = upper_bound = query_size
            while lower_bound >= 0 and trigram_similarity_naive(query, set(islice(query, lower_bound))) >= min_score:
                lower_bound -= 1
            max_int = max(query)
            while trigram_similarity_naive(query, query | {max_int + 1 + i
                                                           for i in range(upper_bound - query_size)}) >= min_score:
                upper_bound += 1

        _TRIGRAM_SIZE_BOUNDS[min_score][query_size] = lower_bound + 1, upper_bound

    return _TRIGRAM_SIZE_BOUNDS[min_score][query_size]
