import re
import warnings
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from text_scrubber.geo.clean import clean_city, clean_country, clean_region
from text_scrubber.geo.resources import (_CITY_RESOURCES, _COUNTRY_RESOURCES, _REGION_RESOURCES,
                                         add_city_resources, add_region_resources)
from text_scrubber.geo.string_distance import find_closest_string, pattern_match


RE_ALPHA = re.compile(r'[a-zA-Z]')


@dataclass(init=True, frozen=True)
class Location:
    canonical_name: str
    matched_name: str
    country: Optional[str]
    score: float


def normalize_country(country: str, min_score_levenshtein: float = 0.8,
                      min_score_trigram: float = 0.5) -> List[Location]:
    """
    Cleans up a country by string cleaning and performs some basic country lookups to get the canonical name.

    Note: when countries are officially part of another country, we return the latter. E.g., Greenland is normalized
    to Denmark.

    :param country: Country string to clean.
    :param min_score_levenshtein: Minimum score to use for Levenshtein similarity
    :param min_score_trigram: Minimum score to use for trigram similarity
    :return: List of LocationMatch candidates sorted by score (desc)
    """
    # Clean country
    cleaned_country = clean_country(country)

    # When have no input after cleaning it should return the original
    if not cleaned_country:
        return []

    canonical_country_names = _COUNTRY_RESOURCES['countries']['canonical_names']

    # Check if country is part of the known countries list
    if cleaned_country in _COUNTRY_RESOURCES['countries']['cleaned_location_map']:
        canonical_country_idx, country_idx = _COUNTRY_RESOURCES['countries']['cleaned_location_map'][cleaned_country]
        return [Location(canonical_name=canonical_country_names[canonical_country_idx],
                         matched_name=canonical_country_names[country_idx], country=None, score=1.0)]

    # Check if the country follows a certain country pattern
    known_country = pattern_match(country, _COUNTRY_RESOURCES['replacement_patterns'])
    if known_country:
        canonical_country_idx, _ = _COUNTRY_RESOURCES['countries']['cleaned_location_map'][known_country]
        return [Location(canonical_name=canonical_country_names[canonical_country_idx],
                         matched_name=capitalize_geo_string(known_country), country=None, score=1.0)]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    country_match = find_closest_string(cleaned_country, _COUNTRY_RESOURCES['countries'],
                                        min_score_levenshtein, min_score_trigram)
    if country_match:
        best_matches, score = country_match
        candidates = [Location(canonical_name=canonical_country_names[canonical_country_idx],
                               matched_name=canonical_country_names[country_idx], country=None, score=score)
                      for canonical_country_idx, country_idx in best_matches]

        # Remove duplicates. E.g., "Netherland" matches to the same country twice: "Netherlands", "The Netherlands"
        deduped_candidates = defaultdict(list)
        for candidate in candidates:
            dedupe_key = (clean_country(candidate.canonical_name), candidate.score)
            deduped_candidates[dedupe_key].append(candidate)
        candidates = [process_multiple_names(candidates) for candidates in deduped_candidates.values()]
        return sorted(candidates, key=lambda x: (-x.score, x.canonical_name))

    # No match found
    return []


def normalize_region(region: str, restrict_countries: Optional[Set] = None, min_score_levenshtein: float = 0.8,
                     min_score_trigram: float = 0.5) -> List[Location]:
    """
    Cleans up a region by string cleaning and performs region lookups to get the canonical name

    :param region: Region name
    :param restrict_countries: A set of countries and/or country codes to restrict the search space
    :param min_score_levenshtein: Minimum score to use for Levenshtein similarity
    :param min_score_trigram: Minimum score to use for trigram similarity
    :return: List of Location candidates sorted by score (desc)
    """
    # Clean region
    cleaned_region = clean_region(region)

    # If the cleaned_region is empty return an empty list
    if not cleaned_region:
        return []

    # Add region resources for countries to search in
    country_codes = (_COUNTRY_RESOURCES['all_country_codes'] if restrict_countries is None else
                     normalize_country_to_country_codes(restrict_countries))
    add_region_resources(country_codes)

    # Check if region is part of the known region list
    candidates = []
    not_found = True
    for country_code in country_codes:
        regions_in_country = _REGION_RESOURCES['regions_per_country_code_map'][country_code]
        if cleaned_region in regions_in_country['cleaned_location_map']:
            # Return the canonical name of the region
            canonical_region_idx, region_idx = regions_in_country['cleaned_location_map'][cleaned_region]
            candidates.append(Location(canonical_name=regions_in_country['canonical_names'][canonical_region_idx],
                                       matched_name=regions_in_country['canonical_names'][region_idx],
                                       country=_COUNTRY_RESOURCES['country_to_normalized_country_map'][country_code],
                                       score=1.0))
            not_found = False

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    if not_found:
        for country_code in country_codes:
            regions_in_country = _REGION_RESOURCES['regions_per_country_code_map'][country_code]
            region_match = find_closest_string(cleaned_region, regions_in_country,
                                               min_score_levenshtein, min_score_trigram)

            if region_match:
                best_matches, score = region_match
                canonical_country = _COUNTRY_RESOURCES['country_to_normalized_country_map'][country_code]
                candidates.extend(Location(canonical_name=regions_in_country['canonical_names'][canonical_region_idx],
                                           matched_name=regions_in_country['canonical_names'][region_idx],
                                           country=canonical_country,
                                           score=score) for canonical_region_idx, region_idx in best_matches)

    # Remove duplicates. Regions are also considered duplicates if the cleaned version is equal.
    deduped_candidates = defaultdict(list)
    for candidate in candidates:
        dedupe_key = (clean_region(candidate.canonical_name), candidate.country, candidate.score)
        deduped_candidates[dedupe_key].append(candidate)
    candidates = [process_multiple_names(candidates) for candidates in deduped_candidates.values()]
    return sorted(candidates, key=lambda x: (-x.score, x.canonical_name, x.country))


def normalize_city(city: str, restrict_countries: Optional[Set] = None, min_score_levenshtein: float = 0.8,
                   min_score_trigram: float = 0.5) -> List[Location]:
    """
    Cleans up a city by string cleaning and performs city lookups to get the canonical name

    :param city: City name
    :param restrict_countries: A set of countries and/or country codes to restrict the search space
    :param min_score_levenshtein: minimum score to use for Levenshtein similarity
    :param min_score_trigram: minimum score to use for trigram similarity
    :return: List of Location candidates sorted by score (desc)
    """
    # Clean city
    cleaned_city = clean_city(city)

    # If the cleaned_city is empty return an empty list
    if not cleaned_city:
        return []

    # Add city resources for countries to search in
    country_codes = (_COUNTRY_RESOURCES['all_country_codes'] if restrict_countries is None else
                     normalize_country_to_country_codes(restrict_countries))
    add_city_resources(country_codes)

    # Check if city is part of the known cities list
    candidates = []
    not_found = True
    for country_code in country_codes:
        cities_in_country = _CITY_RESOURCES['cities_per_country_code_map'][country_code]
        if cleaned_city in cities_in_country['cleaned_location_map']:
            # Return the canonical name of the city
            canonical_city_idx, city_idx = cities_in_country['cleaned_location_map'][cleaned_city]
            candidates.append(Location(canonical_name=cities_in_country['canonical_names'][canonical_city_idx],
                                       matched_name=cities_in_country['canonical_names'][city_idx],
                                       country=_COUNTRY_RESOURCES['country_to_normalized_country_map'][country_code],
                                       score=1.0))
            not_found = False

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    if not_found:
        for country_code in country_codes:
            cities_in_country = _CITY_RESOURCES['cities_per_country_code_map'][country_code]
            city_match = find_closest_string(cleaned_city, cities_in_country,
                                             min_score_levenshtein, min_score_trigram)

            if city_match:
                best_matches, score = city_match
                canonical_country = _COUNTRY_RESOURCES['country_to_normalized_country_map'][country_code]
                candidates.extend(Location(canonical_name=cities_in_country['canonical_names'][canonical_city_idx],
                                           matched_name=cities_in_country['canonical_names'][city_idx],
                                           country=canonical_country,
                                           score=score) for canonical_city_idx, city_idx in best_matches)

    # Remove duplicates such as San Jose (US and Porto Rico). Both of them returns ('San Jose', 'United States', 1.0).
    # Cities are also considered duplicates if the cleaned version is equal.
    deduped_candidates = defaultdict(list)
    for candidate in candidates:
        dedupe_key = (clean_city(candidate.canonical_name), candidate.country, candidate.score)
        deduped_candidates[dedupe_key].append(candidate)
    candidates = [process_multiple_names(candidates) for candidates in deduped_candidates.values()]
    return sorted(candidates, key=lambda x: (-x.score, x.canonical_name, x.country))


def normalize_country_to_country_codes(countries: Optional[Iterable] = None) -> Set:
    """
    Normalizes countries or country codes to the set of corresponding country codes. E.g., 'Denmark' will result in
    {'DK', 'FO', 'GL'} for Denmark, Faroe Islands, and Greenland

    :param countries: Set of countries or country codes
    :return: Set of corresponding country codes
    """
    # Obtain country codes
    country_codes = set()
    countries_not_found = []
    if countries is None:
        country_codes = _COUNTRY_RESOURCES['all_country_codes']
    else:
        for country in countries:
            # Check country code
            if len(country) == 2 and country.upper() in _COUNTRY_RESOURCES['country_to_normalized_country_map']:
                normalized_country = _COUNTRY_RESOURCES['country_to_normalized_country_map'][country.upper()]
            else:
                normalized_country = normalize_country(country)
                normalized_country = normalized_country[0].canonical_name if normalized_country else None
            if normalized_country not in _COUNTRY_RESOURCES['normalized_country_to_country_codes_map']:
                countries_not_found.append(country)
            else:
                country_codes.update(_COUNTRY_RESOURCES['normalized_country_to_country_codes_map'][normalized_country])

    if countries_not_found:
        warnings.warn(f"The following strings are not country names or codes: {countries_not_found}")

    return country_codes


def process_multiple_names(candidates: List[Location]) -> Location:
    """
    Does nothing if the name is already a string. However, in the other case where it's a list of strings we
    determine which variant has the most non-ascii characters and return that one. E.g., [Chenet, Chênet] -> Chênet.
    If there's a tie, we select the longest one. E.g. [Etten, Etten-Leur] -> Etten-Leur. If there's still a tie, we
    return the one with the shortest matched name. E.g. [Netherlands, The Netherlands] -> Netherlands. If there's still
    a tie, sort and return the first one. The other name is added to the alternate names. If they are similar after `
    clean_city`, they will be removed when saving the names to file.

    :param candidates: List of normalized location candidates
    :return: Single best candidate
    """
    sorted_candidates = sorted(((len(RE_ALPHA.sub('', candidate.canonical_name)),
                                 len(candidate.canonical_name),
                                 candidate.canonical_name,
                                 len(candidate.matched_name),
                                 idx)
                                for idx, candidate in enumerate(candidates)),
                               key=lambda tup: (-tup[0], -tup[1], tup[2], tup[3], tup[4]))
    return candidates[sorted_candidates[0][4]]


def capitalize_geo_string(string: str) -> str:
    """
    Capitalizes the first letter of each word in the geo string (excluding the terms 'and' and 'of').

    :param string: The string to capitalize.
    :return: The capitalized string.
    """
    return ' '.join(token if token in {'and', 'of'} else token.capitalize() for token in string.split())
