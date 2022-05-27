import inspect
from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterable, List, Optional, Set

from text_scrubber.geo.clean import clean_city, clean_country, clean_region
from text_scrubber.geo.normalize import Location, normalize_city, normalize_country, normalize_region
from text_scrubber.geo.resources import _COUNTRY_RESOURCES
from text_scrubber.geo.string_distance_levenshtein import find_levenshtein_bounds
from text_scrubber.geo.string_distance_trigrams import find_trigram_bounds


@dataclass(init=True, frozen=True)
class Range:
    start: int
    end: int


@dataclass(init=True, frozen=True)
class ExtractedLocation:
    location: Location
    substring: str
    substring_range: Range


def range_has_overlap(range_1: Optional[Range], range_2: Optional[Range]) -> bool:
    """
    Checks if two ranges overlap based on start_idx and end_idx

    :param range_1: Range object
    :param range_2: Range object
    :return: Boolean indicating whether there is overlap
    """
    if range_1 is None or range_2 is None:
        return False
    return max(range_1.start, range_2.start) < min(range_1.end, range_2.end)


def cumsum(x: Iterable) -> List:
    """
    Replicates numpy.cumsum

    :param x: List of numbers
    :return: List of cumulative sums
    """
    y = []
    summed = 0
    for e in x:
        summed += e
        y.append(summed)

    return y


def _find_in_string(sample: str, clean_func: Callable, normalize_func: Callable, blacklist: Set,
                    whitelist_last_resort: Set, match_threshold: float = 0.84, match_threshold_small: float = 0.90,
                    threshold_small: int = 4, max_tokens_to_consider: int = 4,
                    restrict_countries: Optional[Set] = None) -> List[ExtractedLocation]:
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
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_threshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :param restrict_countries: set of countries to use for limiting the search
    :return: list of possible matches
    """
    # First goes through combinations of 1-max_tokens tokens and applies the normalization function of text_scrubber.geo
    # to check if a candidate is present. We store the start and end idx
    tokens = sample.split()
    token_start_idx = [0] + cumsum((len(token) for token in tokens))
    matches = []
    for n_tokens in range(1, max_tokens_to_consider):
        for start_idx in range(0, len(tokens) + 1 - n_tokens):
            combination = ' '.join(tokens[start_idx:start_idx + n_tokens]).rstrip(' .,-()')

            # Skip blacklisted combinations
            if combination in blacklist or clean_func(combination) in blacklist:
                continue

            # Look for a match
            match = _get_matches(combination, token_start_idx, start_idx, normalize_func, match_threshold,
                                 match_threshold_small, threshold_small, restrict_countries)
            if match is not None:
                matches.append(match)

    # Do the above again, but now without blacklist and only one token
    # the second condition is for speeding up. Since if the blacklist is empty, it doesn't make sense to check the rest
    if not matches and bool(len(blacklist)):
        n_tokens = 1
        for start_idx in range(0, len(tokens) + 1 - n_tokens):
            combination = ' '.join(tokens[start_idx:start_idx + n_tokens]).rstrip(' .,-()')

            # Skip non-whitelisted combinations. We assume they're valid candidates now
            if combination not in whitelist_last_resort:
                continue

            # Look for a match
            match = _get_matches(combination, token_start_idx, start_idx, normalize_func, match_threshold,
                                 match_threshold_small, threshold_small, restrict_countries)
            if match is not None:
                matches.append(match)

    # Sort desc by score
    matches = sorted(matches, key=lambda c: -c.location.score)

    # Determine which matches to keep and which ones to dismiss when there's overlap in substrings.
    # The values in this array are as follows: 0=completely dismissed, 1=uncertain, 2=accepted
    keep_matches = [1 for _ in range(len(matches))]
    while any(match == 1 for match in keep_matches):

        prev = [k for k in keep_matches]
        for idx_1, match_1 in enumerate(matches):

            # Already accepted/dismissed?
            if keep_matches[idx_1] in {0, 2}:
                continue

            # Check if it has no overlap to any following candidate that hasn't yet been dimissed entirely. If there's
            # overlap between results, we take the one with the highest score. If scores are equal, we take the longest
            # normalized one (e.g., 'Guinea' vs 'Papua New Guinea'). If that's also equal, then we take the smallest
            # original string that lead to it (e.g., 'New York 1234' vs 'New York').
            skip_match = False
            for idx_2, match_2 in enumerate(matches[idx_1 + 1:], start=idx_1 + 1):
                if keep_matches[idx_2] != 0 and range_has_overlap(match_1.substring_range, match_2.substring_range):
                    if match_1.location.score > match_2.location.score:
                        continue
                    elif match_1.location.score < match_2.location.score:
                        skip_match = True
                        break

                    if len(match_1.location.canonical_name) > len(match_2.location.canonical_name):
                        continue
                    elif len(match_1.location.canonical_name) < len(match_2.location.canonical_name):
                        skip_match = True
                        break

                    if len(match_1.substring) < len(match_2.substring):
                        continue
                    elif len(match_1.substring) > len(match_2.substring):
                        skip_match = True
                        break

            # If we keep this one, disable others that have overlap
            if not skip_match:
                keep_matches[idx_1] = 2
                for idx_2, match_2 in enumerate(matches):
                    if idx_1 != idx_2 and range_has_overlap(match_1.substring_range, match_2.substring_range):
                        keep_matches[idx_2] = 0

        # Fail-safe to avoid infinite loops. I don't expect there to be any, but just to be safe
        if prev == keep_matches:
            break

    # Filter
    return [c for idx, c in enumerate(matches) if keep_matches[idx] == 2]


def _get_matches(combination: str, token_start_idx: List[int], start_idx: int, normalize_func: Callable,
                 match_threshold: float, match_threshold_small: float, threshold_small: int,
                 restrict_countries: Optional[Set]) -> Optional[ExtractedLocation]:
    """
    Try to find a matching location using the normalization function. If we find any matches, we store the one with the
    highest score and additionally store the start and end idx of the substring. Note that we add start_idx, to
    accommodate for the spaces after each word (which were lost after calling .split()) in the _find_in_string function.

    :param combination: combination string
    :param token_start_idx: list of token start indices
    :param start_idx: start index of the current combination
    :param normalize_func: normalization function for countries/cities/regions
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_threshold_small``, otherwise ``match_threshold``
    :param restrict_countries: set of countries to use for limiting the search
    :return: a matching location when available, None otherwise
    """
    threshold = match_threshold if len(combination) > threshold_small else match_threshold_small
    if restrict_countries is not None:
        matches_found = normalize_func(combination, restrict_countries, min_score_levenshtein=threshold,
                                       min_score_trigram=threshold)
    else:
        matches_found = normalize_func(combination, min_score_levenshtein=threshold,
                                       min_score_trigram=threshold)
    if matches_found:
        match = max(matches_found, key=lambda match_: match_.score)
        str_start_idx = token_start_idx[start_idx] + start_idx
        str_end_idx = str_start_idx + len(combination)
        return ExtractedLocation(location=match, substring=combination,
                                 substring_range=Range(str_start_idx, str_end_idx))


def find_country_in_string(sample: str, match_threshold: float = 0.84, match_threshold_small: float = 0.90,
                           threshold_small: int = 4, max_tokens_to_consider: int = 4) -> List[ExtractedLocation]:
    """
    Extracts countries from a sample text.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    :param sample: text sample
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_threshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of matches
    """
    # We skip certain tokens, as they are too confusing. The whitelist_last_resort is used for when no countries could
    # be found. In that case we do allow to find those strings, if they're uppercase.
    all_country_codes_lower = {cc.lower() for cc in _COUNTRY_RESOURCES['all_country_codes']}
    blacklist = _COUNTRY_RESOURCES['all_country_codes'] | all_country_codes_lower | {'u'}
    whitelist_last_resort = _COUNTRY_RESOURCES['all_country_codes']

    return _find_in_string(sample, clean_country, normalize_country, blacklist, whitelist_last_resort,
                           match_threshold, match_threshold_small, threshold_small, max_tokens_to_consider)


def find_city_in_string(sample: str, country_set: Optional[set] = None, match_threshold: float = 0.84,
                        match_threshold_small: float = 0.90, threshold_small: int = 4,
                        max_tokens_to_consider: int = 6) -> List[ExtractedLocation]:
    """
    Extracts cities from a sample text.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    :param sample: text sample
    :param country_set: Restrict the search to this set of countries
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_threshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of matches
    """
    # We skip certain tokens, as they are too confusing. The whitelist_last_resort is used for when no cities could be
    # found. In that case we do allow to find those strings.
    blacklist = set()
    whitelist_last_resort = set()

    return _find_in_string(sample, clean_city, normalize_city, blacklist, whitelist_last_resort, match_threshold,
                           match_threshold_small, threshold_small, max_tokens_to_consider, country_set)


def find_region_in_string(sample: str, country_set: Optional[set] = None, match_threshold: float = 0.84,
                          match_threshold_small: float = 0.90, threshold_small: int = 4,
                          max_tokens_to_consider: int = 6) -> List[ExtractedLocation]:
    """
    Extracts regions from a sample text.

    Thresholds were derived empirically based on one of our usecases. Change them when needed.

    :param sample: text sample
    :param country_set: Restrict the search to this set of countries
    :param match_threshold: threshold for considering a substring a match
    :param match_threshold_small: threshold for considering a substring a match, applied to smaller normalized countries
    :param threshold_small: if the length of a candidate string is <= ``threshold_small`` it will use the
        ``match_threshold_small``, otherwise ``match_threshold``
    :param max_tokens_to_consider: maximum amount of tokens to consider as a combination for comparing to normalized
        countries
    :return: list of matches
    """
    # We skip certain tokens, as they are too confusing. The whitelist_last_resort is used for when no regions could be
    # found. In that case we do allow to find those strings.
    blacklist = set()
    whitelist_last_resort = set()

    return _find_in_string(sample, clean_region, normalize_region, blacklist, whitelist_last_resort, match_threshold,
                           match_threshold_small, threshold_small, max_tokens_to_consider, country_set)


def _precompute_bounds_find_in_string() -> None:
    """
    Precompute bounds for matching for the `find_in_string` functions. I.e., we find a lower and upper bound for queries
    of varying size (1-50 characters). If a candidate falls outside these bounds, it is guaranteed that the minimum
    score will never be reached. These bounds are stored in global maps.
    """
    # Extract the threshold parameter default values of the find_x_in_string functions so we can precompute bounds based
    # on those thresholds
    country_params = inspect.signature(find_country_in_string).parameters
    region_params = inspect.signature(find_region_in_string).parameters
    city_params = inspect.signature(find_city_in_string).parameters
    for query_size in range(1, 50):
        for params, threshold_name in product((country_params, region_params, city_params),
                                              ('match_threshold', 'match_threshold_small')):
            find_levenshtein_bounds(query_size, params[threshold_name].default)
            find_trigram_bounds(query_size, params[threshold_name].default)


_precompute_bounds_find_in_string()
