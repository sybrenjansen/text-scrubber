from itertools import islice
from typing import Callable, Dict, Iterable, List, Optional, Pattern, Set, Tuple, Union

import Levenshtein


def find_closest_string(string: str, options: Dict[str, Dict[int, Dict[str, Union[str, Set[int]]]]],
                        min_score_levenshtein: float = 0.8,
                        min_score_trigram: float = 0.5) -> Optional[Tuple[List[str], float]]:
    """

    :param string: string to search for
    :param options: {option: trigram tokens} dictionary containing string options with corresponding trigram tokens
    :param min_score_levenshtein: minimum score to use for Levenshtein similarity
    :param min_score_trigram: minimum score to use for trigram similarity
    :return: (best options, score) when minimum score is obtained, None otherwise
    """
    # First try to match using Levenshtein. This will usually be enough for accurate matching
    result = _find_closest_string(string, options['canonical_name'], Levenshtein.ratio, False, min_score_levenshtein)  # TODO: 57.2%

    # If there's no match fall back to trigram matching. Trigram matching is very useful when tokens are in a different
    # order
    if result is None:
        result = _find_closest_string(string, options['trigram_tokens'], _trigram_similarity, True, min_score_trigram)  # TODO: 42.8%

    return result


def _find_closest_string(
    string: str, options: Dict[int, Dict[str, Union[str, Set[int]]]], compare_func: Callable,
        use_trigrams: bool, min_score: float
) -> Optional[Tuple[List[str], float]]:
    """
    Find the closest match for a string from a list of options using Levenshtein edit distance

    :param string: string to search for
    :param options: {option: trigram tokens} dictionary containing string options with corresponding trigram tokens
    :param compare_func: comparison function that returns a similarity score
    :param use_trigrams: whether to use trigrams
    :param min_score: minimum trigram similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: (best options, score) when minimum score is obtained, None otherwise
    """
    # Get trigram tokens for search string
    if use_trigrams:
        string = get_trigram_tokens(string)

    # Obtain bounds
    size_lower_bound, size_upper_bound = _find_bounds(string, compare_func, use_trigrams, min_score)

    # Obtain scores and determine best option taking into account the minimum score threshold
    best_options = []
    best_score = -1.0
    index = 1 if use_trigrams else 0
    for size in range(size_lower_bound, size_upper_bound):
        for option, option_trigrams in options[size].items():  # TODO: 27.7%

            score = compare_func(string, option_trigrams if use_trigrams else option)  # TODO: 51.8%
            if score >= min_score and score >= best_score:  # TODO: 20.5%
                if score == best_score:
                    best_options.append(option)
                else:
                    best_options = [option]
                    best_score = score

    if best_options:
        return best_options, best_score


def _find_bounds(query: Union[str, Set[int]], compare_func: Callable, use_trigrams: bool,
                 min_score: float) -> Tuple[int, int]:
    """
    Finds a lower and upper bound for a given query. If a candidate falls behind these bounds, it is guaranteed that the
    minimum score will never be reached. If the bounds are not known yet it will determine them on the fly.

    :param query: the query
    :param compare_func: comparison function that returns a similarity score
    :param use_trigrams: whether to use trigrams
    :param min_score: minimum trigram similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: lower (inclusive) and upper (exclusive) bound
    """
    global _LEVENSHTEIN_BOUNDS, _TRIGRAM_BOUNDS
    query_size = len(query)

    # Trigrams
    if use_trigrams:
        if min_score not in _TRIGRAM_BOUNDS:
            _TRIGRAM_BOUNDS[min_score] = dict()
        if query_size not in _TRIGRAM_BOUNDS[min_score]:
            lower_bound = upper_bound = query_size
            while lower_bound >= 0 and compare_func(query, set(islice(query, lower_bound))) >= min_score:
                lower_bound -= 1
            max_int = max(query)
            while compare_func(query, query | {max_int + 1 + i for i in range(upper_bound - query_size)}) >= min_score:
                upper_bound += 1
            _TRIGRAM_BOUNDS[min_score][query_size] = lower_bound + 1, upper_bound
        return _TRIGRAM_BOUNDS[min_score][query_size]

    # Levenshtein
    else:
        if min_score not in _LEVENSHTEIN_BOUNDS:
            _LEVENSHTEIN_BOUNDS[min_score] = dict()
        if query_size not in _LEVENSHTEIN_BOUNDS[min_score]:
            lower_bound = upper_bound = query_size
            while lower_bound >= 0 and compare_func(query, query[:lower_bound]) >= min_score:
                lower_bound -= 1
            while compare_func(query, query + 'a' * (upper_bound - query_size)) >= min_score:
                upper_bound += 1
            _LEVENSHTEIN_BOUNDS[min_score][query_size] = lower_bound + 1, upper_bound
        return _LEVENSHTEIN_BOUNDS[min_score][query_size]


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


def _trigram_similarity(string_trigrams: Set[str], option_trigrams: Set[str]) -> float:
    """
    Computes the trigram similarity

    :param string_trigrams: set of trigrams belonging to the search string
    :param option_trigrams: set of trigrams belonging to the option
    :return: trigram similarity
    """
    n_overlap = len(string_trigrams & option_trigrams)
    return n_overlap / (len(string_trigrams) + len(option_trigrams) - n_overlap)


def pattern_match(string: str, patterns: Iterable[Tuple[Pattern[str], str]]) -> Optional[str]:
    """
    Returns the replacement string when a pattern matches the string query

    :param string: string to search for
    :param patterns: iterable of (regex patterns, replacement string) tuples
    :return: replacement string of the fist pattern that matches, None if there's no match
    """
    for pattern, replacement_str in patterns:
        if pattern.match(string):
            return replacement_str


# Global trigram map for storing {trigram: trigram ID} to save memory
_TRIGRAM_MAP = {}

# Bounds for Levenshtein and trigram distances
_LEVENSHTEIN_BOUNDS = dict()
_TRIGRAM_BOUNDS = dict()
