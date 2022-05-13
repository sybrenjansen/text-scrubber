import re
from collections import defaultdict

from tqdm import tqdm
from typing import Any, List, Tuple, Dict, Optional, Set, Union
import warnings

from text_scrubber import TextScrubber
from text_scrubber.io import read_resource_file, read_resource_json_file
from text_scrubber.string_distance import find_closest_string, get_trigram_tokens, pattern_match


def normalize_country(country: str, min_score_levenshtein: float = 0.8,
                      min_score_trigram: float = 0.5) -> List[Tuple[str, float]]:
    """
    Cleans up a country by string cleaning and performs some basic country lookups to get the canonical name.

    Note: when countries are officially part of another country, we return the latter. E.g., Greenland is normalized
    to Denmark.

    :param country: Country string to clean.
    :param min_score_levenshtein: minimum score to use for Levenshtein similarity
    :param min_score_trigram: minimum score to use for trigram similarity
    :return: List of (country, score) candidates in canonical form, sorted by score (desc)
    """
    # Clean country
    cleaned_country = clean_country(country)

    # When have no input after cleaning it should return the original
    if not cleaned_country:
        return []

    # Check if country is part of the known countries list
    for countries in _COUNTRY_RESOURCES['countries']['canonical_name'].values():
        if cleaned_country in countries:
            candidate = countries[cleaned_country]
            return [(candidate, 1.0)]

    # There's a number of known expansions/translations which can be applied. Check if we can find anything with that
    if cleaned_country in _COUNTRY_RESOURCES['replacements']:
        replacement = _COUNTRY_RESOURCES['replacements'][cleaned_country]
        candidate = _COUNTRY_RESOURCES['countries']['canonical_name'][len(replacement)][replacement]
        return [(candidate, 1.0)]

    # Check if the country follows a certain country pattern
    known_country = pattern_match(country, _COUNTRY_RESOURCES['replacement_patterns'])
    if known_country:
        candidate = _COUNTRY_RESOURCES['countries']['canonical_name'][len(known_country)][known_country]
        return [(candidate, 1.0)]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    country_match = find_closest_string(cleaned_country, _COUNTRY_RESOURCES['countries'],
                                        min_score_levenshtein, min_score_trigram)
    if country_match:
        best_matches, score = country_match
        candidates = (_COUNTRY_RESOURCES['countries']['canonical_name'][len(country)][country]
                      for country in best_matches)
        return [(candidate, score) for candidate in candidates]

    # No match found
    return []


def normalize_region(region: str, restrict_countries: Optional[Set] = None, min_score_levenshtein: float = 0.8,
                     min_score_trigram: float = 0.5) -> List[Tuple[str, str, float]]:
    """
    Cleans up a region by string cleaning and performs region lookups to get the canonical name

    :param restrict_countries: A set of countries and/or country codes to restrict the search space
    :param region: City name
    :param min_score_levenshtein: minimum score to use for Levenshtein similarity
    :param min_score_trigram: minimum score to use for trigram similarity
    :return: List of (city, country, score) candidates in canonical form, sorted by score (desc)
    """
    # Clean region
    cleaned_region = clean_region(region)

    # If the cleaned_region is empty return an empty list
    if not cleaned_region:
        return []

    # Add region resources for countries to search in
    add_region_resources(restrict_countries)
    country_codes = (_REGION_RESOURCES['all_country_codes'] if restrict_countries is None else
                     _normalize_country_to_country_codes(restrict_countries))

    # Check if region is part of the known region list
    candidates = []
    not_found = True
    for country_code in country_codes:
        regions_in_country = _REGION_RESOURCES['regions_per_country_code_map'][country_code]
        for regions in regions_in_country['canonical_name'].values():
            if cleaned_region in regions:
                # Return the exact name of the region
                capitalized_region = regions[cleaned_region]
                capitalize_country = _REGION_RESOURCES['country_to_normalized_country_map'][country_code]
                candidates.append((capitalized_region, capitalize_country, 1.0))
                not_found = False

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    if not_found:
        for country_code in country_codes:
            regions_in_country = _REGION_RESOURCES['regions_per_country_code_map'][country_code]
            region_match = find_closest_string(cleaned_region, regions_in_country,
                                               min_score_levenshtein, min_score_trigram)

            if region_match:
                best_matches, score = region_match
                best_matches = [regions_in_country['canonical_name'][len(best_match)][best_match]
                                for best_match in best_matches]
                capitalize_country = _REGION_RESOURCES['country_to_normalized_country_map'][country_code]
                for best_match in best_matches:
                    candidates.append((best_match, capitalize_country, score))

    # Remove duplicates. Regions are also considered duplicates if the cleaned version is equal.
    deduped_candidates = defaultdict(list)
    for region, country, score in candidates:
        deduped_candidates[(clean_region(region), country, score)].append(region)
    candidates = [(process_multiple_names(names) if len(names) > 1 else names[0], country, score)
                  for (_, country, score), names in deduped_candidates.items()]
    return sorted(candidates, key=lambda x: (-x[2], x[0], x[1]))


def normalize_city(city: str, restrict_countries: Optional[Set] = None, min_score_levenshtein: float = 0.8,
                   min_score_trigram: float = 0.5) -> List[Tuple[str, str, float]]:
    """
    Cleans up a city by string cleaning and performs city lookups to get the canonical name

    :param city: City name
    :param restrict_countries: A set of countries and/or country codes to restrict the search space
    :param min_score_levenshtein: minimum score to use for Levenshtein similarity
    :param min_score_trigram: minimum score to use for trigram similarity
    :return: List of (city, country, score) candidates in canonical form, sorted by score (desc)
    """
    # Clean city
    cleaned_city = clean_city(city)

    # If the cleaned_city is empty return an empty list
    if not cleaned_city:
        return []

    # Add city resources for countries to search in
    add_city_resources(restrict_countries)
    country_codes = (_CITY_RESOURCES['all_country_codes'] if restrict_countries is None else
                     _normalize_country_to_country_codes(restrict_countries))

    # Check if city is part of the known cities list
    candidates = []
    not_found = True
    for country_code in country_codes:
        cities_in_country = _CITY_RESOURCES['cities_per_country_code_map'][country_code]
        for cities in cities_in_country['canonical_name'].values():
            if cleaned_city in cities:
                # Return the exact name of the city
                capitalized_city = cities[cleaned_city]
                capitalize_country = _CITY_RESOURCES['country_to_normalized_country_map'][country_code]
                candidates.append((capitalized_city, capitalize_country, 1.0))
                not_found = False

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    if not_found:
        for country_code in country_codes:
            cities_in_country = _CITY_RESOURCES['cities_per_country_code_map'][country_code]
            city_match = find_closest_string(cleaned_city, cities_in_country,
                                             min_score_levenshtein, min_score_trigram)

            if city_match:
                best_matches, score = city_match
                best_matches = [cities_in_country['canonical_name'][len(best_match)][best_match]
                                for best_match in best_matches]
                capitalize_country = _CITY_RESOURCES['country_to_normalized_country_map'][country_code]
                for best_match in best_matches:
                    candidates.append((best_match, capitalize_country, score))

    # Remove duplicates such as San Jose (US and Porto Rico). Both of them returns ('San Jose', 'United States', 1.0).
    # Cities are also considered duplicates if the cleaned version is equal.
    deduped_candidates = defaultdict(list)
    for city, country, score in candidates:
        deduped_candidates[(clean_city(city), country, score)].append(city)
    candidates = [(process_multiple_names(names) if len(names) > 1 else names[0], country, score)
                  for (_, country, score), names in deduped_candidates.items()]
    return sorted(candidates, key=lambda x: (-x[2], x[0], x[1]))


def process_multiple_names(names: List[str]):
    """
    Does nothing if the name is already a string. However, in the other case where it's a list of strings we
    determine which variant has the most non-ascii characters and return that one. E.g., [Chenet, Chênet] -> Chênet.
    If there's a tie, we select the longest one. E.g. [Etten, Etten-Leur] -> Etten-Leur. If there's still a tie,
    sort and return the first one. The other name is added to the alternate names. If they are similar after `
    clean_city`, they will be removed when saving the names to file.

    :param names: List of city/region names
    :return: Single unified name
    """
    names = sorted(((len(RE_ALPHA.sub('', name)), len(name), name) for name in names),
                   key=lambda tup: (-tup[0], -tup[1], tup[2]))
    return names[0][2]


RE_ALPHA = re.compile(r'[a-zA-Z]')

# Some common token replacements
_GEO_TOKEN_MAP = {'afr': 'african',
                  'brit': 'brittish',
                  'cent': 'central',
                  'dem': 'democratic',
                  'equat': 'equatorial',
                  'is': 'islands',
                  'isl': 'islands',
                  'isla': 'islands',
                  'island': 'islands',
                  'monteneg': 'montenegro',
                  'neth': 'netherlands',
                  'rep': 'republic',
                  'republ': 'republic',
                  'republik': 'republic',
                  'sint': 'saint',
                  'st': 'saint',
                  'ter': 'territory',
                  'territories': 'territory'}

# We define the scrubber once so the regex objects will be compiled only once
_GEO_STRING_SCRUBBER = (TextScrubber().to_ascii()
                                      .remove_digits()
                                      .sub(r'-|/|&|,', ' ')
                                      .remove_punctuation()
                                      .tokenize()
                                      .remove_stop_words({'a', 'an', 'and', 'der', 'da', 'di', 'do', 'e', 'le', 'im',
                                                          'mail'}, case_sensitive=True)
                                      .lowercase(on_tokens=True)
                                      .filter_tokens()
                                      .sub_tokens(lambda token: _GEO_TOKEN_MAP.get(token, token))
                                      .remove_stop_words({'cedex', 'email', 'of', 'the'})
                                      .join())


def _clean_geo_string(string: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    Cleans a strings with geographical information (e.g., countries/regions/cities).

    :param string: Input string to clean.
    :return: Cleaned string.
    """
    return _GEO_STRING_SCRUBBER.transform(string)


# Same cleaning is used for countries, regions, and cities
clean_country = clean_region = clean_city = _clean_geo_string


def capitalize_geo_string(string: str) -> str:
    """
    Capitalizes the first letter of each word in the geo string (excluding the terms 'and' and 'of').

    :param string: The string to capitalize.
    :return: The capitalized string.
    """
    return ' '.join(token if token in {'and', 'of'} else token.capitalize() for token in string.split())


def _get_country_resources() -> Dict[str, Dict]:
    """
    Reads and parses country resource files.

    :return: Dictionary containing resources used for country normalization.
    """
    resources = dict()

    # Read in a map of common country name replacements
    replacements_file = (line.split(", ") for line in read_resource_file(__file__, 'resources/country_map.txt'))
    resources['replacements'] = {clean_country(country): clean_country(canonical_country)
                                 for country, canonical_country in replacements_file}

    # Replacement patterns additional to the other replacements (mainly filters zipcodes)
    resources['replacement_patterns'] = [(pattern, clean_country(canonical_country)) for pattern, canonical_country in
                                         ((re.compile(r'\d+[a-z]+\d+ canada [a-z]+\d+[a-z]+', re.IGNORECASE), 'canada'),
                                          (re.compile(r'\d+ russia', re.IGNORECASE), 'russia'))]

    # Get a map of cleaned country name to canonical country name, and generate trigrams
    resources['countries'] = {'canonical_name': defaultdict(dict), 'trigram_tokens': defaultdict(dict)}
    for canonical_country in read_resource_json_file(__file__, "resources/norm_country_country_codes_map.json").keys():
        cleaned_country = clean_country(canonical_country)
        trigram_tokens = get_trigram_tokens(cleaned_country)
        resources['countries']['canonical_name'][len(cleaned_country)][cleaned_country] = canonical_country
        resources['countries']['trigram_tokens'][len(trigram_tokens)][cleaned_country] = trigram_tokens

    return resources


_COUNTRY_RESOURCES = _get_country_resources()


def _get_initial_region_resources() -> Dict[str, Any]:
    """
    Reads and parses region resource files

    :return: Dictionary containing resources used for region normalization
    """
    resources = dict()

    resources['country_to_normalized_country_map'] = read_resource_json_file(
        __file__, "resources/country_norm_country_map.json"
    )
    resources['normalized_country_to_country_codes_map'] = read_resource_json_file(
        __file__, "resources/norm_country_country_codes_map.json"
    )
    resources['all_country_codes'] = {
        country_code for country_codes in resources['normalized_country_to_country_codes_map'].values()
        for country_code in country_codes
    }

    # Placeholder
    resources['regions_per_country_code_map'] = dict()

    return resources


_REGION_RESOURCES = _get_initial_region_resources()


def _get_initial_city_resources() -> Dict[str, Any]:
    """
    Reads and parses city resource files

    :return: Dictionary containing resources used for city normalization
    """
    resources = dict()

    resources['country_to_normalized_country_map'] = read_resource_json_file(
        __file__, "resources/country_norm_country_map.json"
    )
    resources['normalized_country_to_country_codes_map'] = read_resource_json_file(
        __file__, "resources/norm_country_country_codes_map.json"
    )
    resources['all_country_codes'] = {
        country_code for country_codes in resources['normalized_country_to_country_codes_map'].values()
        for country_code in country_codes
    }

    # Placeholder
    resources['cities_per_country_code_map'] = dict()

    return resources


_CITY_RESOURCES = _get_initial_city_resources()


def _normalize_country_to_country_codes(countries: Optional[Set] = None) -> Set:
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
        country_codes = _CITY_RESOURCES['all_country_codes']
    else:
        for country in countries:
            # Check country code
            if len(country) == 2 and country.upper() in _CITY_RESOURCES['country_to_normalized_country_map']:
                normalized_country = _CITY_RESOURCES['country_to_normalized_country_map'][country.upper()]
            else:
                normalized_country = normalize_country(country)
                normalized_country = normalized_country[0][0] if normalized_country else None
            if normalized_country not in _CITY_RESOURCES['normalized_country_to_country_codes_map']:
                countries_not_found.append(country)
            else:
                country_codes.update(_CITY_RESOURCES['normalized_country_to_country_codes_map'][normalized_country])

    if countries_not_found:
        warnings.warn(f"The following strings are not country names or codes: {countries_not_found}")

    return country_codes


def add_region_resources(countries: Optional[Set] = None, progress_bar: bool = False) -> None:
    """
    Read and parse region resources for new countries

    :param countries: Only load the list of countries or country codes provided
    :param progress_bar: disable or enable progressbar. Default is no progressbar (False)
    """
    global _REGION_RESOURCES

    # Obtain corresponding country codes
    country_codes = _normalize_country_to_country_codes(countries)

    # Load resources for each country code and update the global resources
    for country_code in tqdm(country_codes, disable=not progress_bar):

        # Skip countries that are already loaded
        if country_code in _REGION_RESOURCES['regions_per_country_code_map']:
            continue

        regions = read_resource_file(__file__, f"resources/regions_per_country/{country_code}.txt")
        region_dict = {'canonical_name': defaultdict(dict), 'trigram_tokens': defaultdict(dict)}
        for region_list in regions:
            # A single line can have multiple alternative spellings of the same city. The first spelling is the
            # canonical one and all versions will point to that
            region_list = region_list.split(", ")
            canonical_region_name = region_list[0]
            for cleaned_region in clean_region(region_list):
                # Sometimes clean_region removes the whole string
                if not cleaned_region:
                    continue
                trigram_tokens = get_trigram_tokens(cleaned_region)
                region_dict['canonical_name'][len(cleaned_region)][cleaned_region] = canonical_region_name
                region_dict['trigram_tokens'][len(trigram_tokens)][cleaned_region] = trigram_tokens

        _REGION_RESOURCES["regions_per_country_code_map"][country_code] = region_dict


def add_city_resources(countries: Optional[Set] = None, progress_bar: bool = False) -> None:
    """
    Read and parse city resources for new countries

    :param countries: Only load the list of countries or country codes provided
    :param progress_bar: disable or enable progressbar. Default is no progressbar (False)
    """
    global _CITY_RESOURCES

    # Obtain corresponding country codes
    country_codes = _normalize_country_to_country_codes(countries)

    # Load resources for each country code and update the global resources
    for country_code in tqdm(country_codes, disable=not progress_bar):

        # Skip countries that are already loaded
        if country_code in _CITY_RESOURCES['cities_per_country_code_map']:
            continue

        cities = read_resource_file(__file__, f"resources/cities_per_country/{country_code}.txt")
        cities_dict = {'canonical_name': defaultdict(dict), 'trigram_tokens': defaultdict(dict)}

        for city_list in cities:
            # A single line can have multiple alternative spellings of the same city. The first spelling is the
            # canonical one and all versions will point to that
            city_list = city_list.split(", ")
            canonical_city_name = city_list[0]
            for cleaned_city in clean_city(city_list):
                # Sometimes clean_city removes the whole string
                if not cleaned_city:
                    continue
                trigram_tokens = get_trigram_tokens(cleaned_city)
                cities_dict['canonical_name'][len(cleaned_city)][cleaned_city] = canonical_city_name
                cities_dict['trigram_tokens'][len(trigram_tokens)][cleaned_city] = trigram_tokens

        _CITY_RESOURCES["cities_per_country_code_map"][country_code] = cities_dict
