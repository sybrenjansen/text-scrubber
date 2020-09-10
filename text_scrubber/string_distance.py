from typing import Callable, Dict, Iterable, List, Optional, Pattern, Set, Tuple

import Levenshtein


def find_closest_string(string: str, options: Dict[str, Set[str]]) -> Optional[Tuple[List[str], float]]:
    """

    :param string: string to search for
    :param options: {option: trigram tokens} dictionary containing string options with corresponding trigram tokens
    :return: (best options, score) when minimum score is obtained, None otherwise
    """
    # First try to match using Levenshtein. This will usually be enough for accurate matching
    result = _find_closest_string(string, options, Levenshtein.ratio, False, 0.8)

    # If there's no match fall back to trigram matching. Trigram matching is very useful when tokens are in a different
    # order
    if result is None:
        result = _find_closest_string(string, options, _trigram_similarity, True, 0.5)

    return result


def _find_closest_string(string: str, options: Dict[str, Set[str]], compare_func: Callable,
                         use_trigrams: bool, min_score: float) -> Optional[Tuple[List[str], float]]:
    """
    Find the closest match for a string from a list of options using Levenshtein edit distance

    :param string: string to search for
    :param options: {option: trigram tokens} dictionary containing string options with corresponding trigram tokens
    :param compare_func:
    :param use_trigrams:
    :param min_score: minimum trigram similarity score to obtain (between 0.0-1.0, 1.0 being a perfect match)
    :return: (best options, score) when minimum score is obtained, None otherwise
    """
    # Get trigram tokens for search string
    if use_trigrams:
        string = get_trigram_tokens(string)

    # Obtain scores and determine best option taking into account the minimum score threshold
    best_options = []
    best_score = None
    for option, option_trigrams in options.items():
        score = compare_func(string, option_trigrams if use_trigrams else option)
        if score >= min_score and (best_score is None or score >= best_score):
            if score == best_score:
                best_options.append(option)
            else:
                best_options = [option]
                best_score = score

    if best_options:
        return best_options, best_score


def get_trigram_tokens(string: str) -> Set[str]:
    """
    Obtain a set of trigram tokens from a string. E.g., 'hello world' --> {'  h', ' he', 'hel', 'ell', 'llo', 'lo ',
    'o  ', '  w', ' wo', 'wor', 'orl', 'rld', 'ld ', 'd  '}

    :param string: string to extract trigrams from
    :return: set of trigrams
    """
    string = f"  {string.replace(' ', '  ')}  "
    return {string[i:i + 3] for i in range(len(string) - 2)}


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
