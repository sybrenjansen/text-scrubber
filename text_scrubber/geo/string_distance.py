from typing import Dict, Iterable, List, Optional, Pattern, Set, Tuple, Union

from scipy.sparse import csr_matrix

from text_scrubber.geo.string_distance_levenshtein import find_closest_string_levenshtein
from text_scrubber.geo.string_distance_trigrams import find_closest_string_trigrams


def find_closest_string(query: str,
                        candidates: Dict[str, Dict[int, Dict[str, Union[str, Set[int], List[int], csr_matrix]]]],
                        min_score_levenshtein: float = 0.8,
                        min_score_trigram: float = 0.5) -> Optional[Tuple[List[int], float]]:
    """
    From a selection of candidates return the best matching ones. First Levenshtein is used, then trigram distance if
    the former didn't yield a good match.

    :param query: string to search for
    :param candidates: candidate dictionary containing 'levenshtein' and 'trigrams' as keys, followed by a
        {size: candidates} dictionary containing candidate information per size
    :param min_score_levenshtein: minimum score to use for Levenshtein similarity
    :param min_score_trigram: minimum score to use for trigram similarity
    :return: (best options, score) when minimum score is obtained, None otherwise
    """
    # First try to match using Levenshtein. This will usually be enough for accurate matching
    result = find_closest_string_levenshtein(query, candidates['levenshtein'], min_score_levenshtein)

    # If there's no match fall back to trigram matching. Trigram matching is very useful when tokens are in a different
    # order
    if result is None:
        result = find_closest_string_trigrams(query, candidates['trigrams'], min_score_trigram)

    return result


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
