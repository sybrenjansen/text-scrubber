from collections import namedtuple
from typing import Callable, List, Optional, Set, Tuple

import numpy as np

from text_scrubber.geo.geo import (clean_city, clean_country, clean_state,
                                   normalize_city, normalize_country, normalize_state)

# Tuple containing start and end idx
Range = Tuple[int, int]

# Match object. 'substring_range' is a tuple denoting the start and end idx of the substring in the original string.
Match = namedtuple('Match', ['substring_range', 'substring', 'normalized', 'score'])


# TODO: we need write unittests for all functions in this file

def _range_has_overlap(range_1: Optional[Range], range_2: Optional[Range]) -> bool:
    """
    Checks if two ranges overlap based on start_idx and end_idx

    :param range_1: (start, end) range tuple
    :param range_2: (start, end) range tuple
    :return: Boolean indicating whether there is overlap
    """
    if range_1 is None or range_2 is None:
        return False
    start_1, end_1 = range_1
    start_2, end_2 = range_2
    return max(start_1, start_2) < min(end_1, end_2)


def _find_in_string(sample: str, clean_func: Callable, normalize_func: Callable, blacklist: Set,
                    whitelist_last_resort: Set, match_threshold: float = 0.84, match_treshold_small: float = 0.90,
                    threshold_small: int = 4, max_tokens_to_consider: int = 4) -> List[Match]:
    """
    Extracts countries from a sample.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    Inner workings:
    - The sample string can consist of any number of tokens (words) and we go through consecutive combinations of them.
      E.g., when the sample is "A B C D" and ``max_tokens_to_consider=2`` we go through the combinations {"A", "B", "C",
      "D", "A B", "B C", "C D"}
    - For each combination we check if it occurs in the blacklist. If so, we skip it
    - Next, we normalize the combination (e.g., using ``normalize_country``), which returns potential matches. These
      matches are thresholded (threshold depends on size of the candidate string). If it exceeds the threshold, the
      location of the combination is stored, together with the score and matching entity.
    - If the above doesn't yield any matches, we disregard the blacklist and use `whitelist_last_resort` with 1 token
      only. E.g., when "IN" can be a country code, but it's usually a stop word.
    - After finding matches, any overlap between matches is resolved using some rules

    :param sample: text sample
    :param clean_func: clean function to use (e.g., clean_country)
    :param normalize_func: normalization function to use (e.g., normalize_country)
    :param blacklist: blacklisted candidates
    :param whitelist_last_resort: list of candidates that we can still consider, but only if we can't match any other
        candidate. E.g., this can be uppercase abbreviations of countries ('US', 'DE', 'IN', ...)
    :param match_threshold: threshold for considering a substring a match
    :param match_treshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_treshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of possible matches
    """
    # First goes through combinations of 1-max_tokens tokens and applies the normalization function of text_scrubber.geo
    # to check if a candidate is present. We store the start and end idx
    tokens = sample.split()
    token_start_idx = [0] + np.cumsum([len(token) for token in tokens]).tolist()
    matches = []
    for n_tokens in range(1, max_tokens_to_consider):
        for start_idx in range(0, len(tokens) + 1 - n_tokens):
            combination = ' '.join(tokens[start_idx:start_idx + n_tokens]).rstrip(' .,-()')

            # Skip blacklisted combinations
            if combination in blacklist or clean_func(combination) in blacklist:
                continue

            # If we find any matches, we store the one with the highest score and additionally store the start and end
            # idx of the substring. Note that we add start_idx, to accommodate for the spaces after each word (which
            # were lost after calling .split())
            matches_found = normalize_func(combination, return_scores=True)
            if matches_found:
                # Threshold
                normalized_match, score = max(matches_found, key=lambda tup: tup[1])
                if score < (match_threshold if len(normalized_match) > threshold_small else match_treshold_small):
                    continue

                str_start_idx = token_start_idx[start_idx] + start_idx
                str_end_idx = str_start_idx + len(combination)
                matches.append(Match(substring_range=(str_start_idx, str_end_idx), substring=combination,
                                     normalized=normalized_match, score=score))

    # Do the above again, but now without blacklist and only one token
    if not matches:
        n_tokens = 1
        for start_idx in range(0, len(tokens) + 1 - n_tokens):
            combination = ' '.join(tokens[start_idx:start_idx + n_tokens]).rstrip(' .,-()')

            # Skip non-whitelisted combinations. We assume they're valid candidates now
            if combination not in whitelist_last_resort:
                continue

            # If we find any matches, we store the one with the highest score and additionally store the start and end
            # idx of the substring. Note that we add start_idx, to accommodate for the spaces after each word (which
            # were lost after calling .split())
            matches_found = normalize_country(combination, return_scores=True)
            if matches_found:
                normalized_match, score = max(matches_found, key=lambda tup: tup[1])
                str_start_idx = token_start_idx[start_idx] + start_idx
                str_end_idx = str_start_idx + len(combination)
                matches.append(Match(substring_range=(str_start_idx, str_end_idx), substring=combination,
                                     normalized=normalized_match, score=score))

    # Sort desc by score
    matches = sorted(matches, key=lambda c: -c.score)

    # If there's overlap between results, we take the one with the highest score. If scores are equal, we take the
    # longest normalized one (e.g., 'Guinea' vs 'Papua New Guinea'). If that's also equal, then we take the smallest
    # original string that lead to it.
    keep_matches = [True for _ in range(len(matches))]
    for idx_1, match_1 in enumerate(matches):

        # Already dismissed?
        if not keep_matches[idx_1]:
            continue

        # Check if it has no overlap to any following candidate. If so, check if we need to keep this one
        for match_2 in matches[idx_1 + 1:]:
            if _range_has_overlap(match_1.substring_range, match_2.substring_range):
                if match_1.score > match_2.score:
                    continue
                elif match_1.score < match_2.score:
                    keep_matches[idx_1] = False
                    continue

                if len(match_1.normalized) > len(match_2.normalized):
                    continue
                elif len(match_1.normalized) < len(match_2.normalized):
                    keep_matches[idx_1] = False
                    continue

                if len(match_1.substring) < len(match_2.substring):
                    continue
                elif len(match_1.substring) > len(match_2.substring):
                    keep_matches[idx_1] = False
                    continue

        # If we keep this one, disable others that have overlap
        if keep_matches[idx_1]:
            for idx_2, match_2 in enumerate(matches[idx_1 + 1:], start=idx_1 + 1):
                if _range_has_overlap(match_1.substring_range, match_2.substring_range):
                    keep_matches[idx_2] = False

    # Filter
    return [c for idx, c in enumerate(matches) if keep_matches[idx]]


def find_country_in_string(sample: str, match_threshold: float = 0.84, match_threshold_small: float = 0.90,
                           threshold_small: int = 4, max_tokens_to_consider: int = 4) -> List[Match]:
    """
    Extracts countries from a sample text.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    :param sample: text sample
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_treshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of possible matches
    """
    # We skip certain tokens, as they are too confusing. The whitelist_last_resort is used for when no countries could
    # be found. In that case we do allow to find those strings, if they're uppercase.
    blacklist = {'at', 'de', 'in', 'u'}
    whitelist_last_resort = {'AT', 'DE', 'IN'}

    return _find_in_string(sample, clean_country, normalize_country, blacklist, whitelist_last_resort, match_threshold,
                           match_threshold_small, threshold_small, max_tokens_to_consider)


def find_city_in_string(sample: str, match_threshold: float = 0.84, match_threshold_small: float = 0.90,
                        threshold_small: int = 4, max_tokens_to_consider: int = 6) -> List[Match]:
    """
    Extracts cities from a sample text.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    :param sample: text sample
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_treshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of possible matches
    """
    # We skip certain tokens, as they are too confusing. The whitelist_last_resort is used for when no cities could be
    # found. In that case we do allow to find those strings.
    blacklist = set()
    whitelist_last_resort = set()

    return _find_in_string(sample, clean_city, normalize_city, blacklist, whitelist_last_resort, match_threshold,
                           match_threshold_small, threshold_small, max_tokens_to_consider)


def find_state_in_string(sample: str, match_threshold: float = 0.84, match_threshold_small: float = 0.90,
                         threshold_small: int = 4, max_tokens_to_consider: int = 6) -> List[Match]:
    """
    Extracts states from a sample text.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    :param sample: text sample
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_treshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of possible matches
    """
    # We skip certain tokens, as they are too confusing. The whitelist_last_resort is used for when no states could be
    # found. In that case we do allow to find those strings.
    blacklist = set()
    whitelist_last_resort = set()

    return _find_in_string(sample, clean_state, normalize_state, blacklist, whitelist_last_resort, match_threshold,
                           match_threshold_small, threshold_small, max_tokens_to_consider)
