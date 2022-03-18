import re
from collections import defaultdict
from tqdm import tqdm
from typing import Any, List, Tuple, Dict, Optional, Set
import warnings

from text_scrubber import TextScrubber
from text_scrubber.io import read_resource_file, read_resource_json_file
from text_scrubber.string_distance import find_closest_string, get_trigram_tokens, pattern_match


def normalize_country(country: str) -> List[Tuple[str, float]]:
    """
    Cleans up a country by string cleaning and performs some basic country lookups to get the canonical name.

    Note: when countries are officially part of another country, we return the latter. E.g., Greenland is normalized
    to Denmark.

    :param country: Country string to clean.
    :return: List of (country, score) candidates in canonical form, sorted by score (desc)
    """
    # Clean country
    cleaned_country = clean_country(country)

    # When have no input after cleaning it should return the original
    if not cleaned_country:
        return []

    # Check if country is part of the known countries list
    if cleaned_country in _COUNTRY_RESOURCES['cleaned_to_capitilized']:
        candidate = _COUNTRY_RESOURCES['cleaned_to_capitilized'][cleaned_country]
        return [(candidate, 1.0)]

    # There's a number of known expansions/translations which can be applied. Check if we can find anything with that
    if cleaned_country in _COUNTRY_RESOURCES['replacements']:
        candidate = _COUNTRY_RESOURCES['cleaned_to_capitilized'][_COUNTRY_RESOURCES['replacements'][cleaned_country]]
        return [(candidate, 1.0)]

    # Check if the country follows a certain country pattern
    known_country = pattern_match(country, _COUNTRY_RESOURCES['replacement_patterns'])
    if known_country:
        candidate = _COUNTRY_RESOURCES['cleaned_to_capitilized'][known_country]
        return [(candidate, 1.0)]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    country_match = find_closest_string(cleaned_country, _COUNTRY_RESOURCES['cleaned_trigrams'])
    if country_match:
        best_matches, score = country_match
        candidates = (_COUNTRY_RESOURCES['cleaned_to_capitilized'][country] for country in best_matches)
        return [(candidate, score) for candidate in candidates]

    # No match found
    return []


def normalize_state(state: str) -> List[Tuple[str, str, float]]:
    """
    Cleans up a state by string cleaning and performs some basic state lookups to get the canonical name.

    Note: states aren't complete!

    :param state: State name or code.
    :return: List of (state, country, score) candidates in canonical form, sorted by score (desc)
    """
    # Clean state
    cleaned_state = clean_state(state)

    # Check if state is part of the known states list
    if cleaned_state in _STATE_RESOURCES['state_country_map']:
        candidates = _STATE_RESOURCES['state_country_map'][cleaned_state]
        candidates = [(candidate, 1.0) for candidate in candidates]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    else:
        state_match = find_closest_string(cleaned_state, _STATE_RESOURCES['cleaned_trigrams'])
        if state_match:
            best_matches, score = state_match
            candidates = (candidate for state in best_matches
                          for candidate in _STATE_RESOURCES['state_country_map'][state])
            candidates = [(candidate, score) for candidate in candidates]
        else:
            # No match found
            candidates = []

    # Return canonical form
    return sorted((state, _COUNTRY_RESOURCES['cleaned_to_capitilized'][country], score)
                  for (state, country), score in candidates)


def normalize_city(city: str, restrict_countries: Optional[Set] = None) -> List[Tuple[str, str, float]]:
    """
    Cleans up a city by string cleaning and performs some city lookups to get the canonical name

    :param restrict_countries: A set of countries and/or country codes to restrict the search space
    :param city: City name
    :return: List of (city, country, score) candidates in canonical form, sorted by score (desc)
    """
    # Clean city
    cleaned_city = clean_city(city)
    # if the cleaned_city is empty return an empty list
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
        if cleaned_city in cities_in_country:
            # Return the exact name of the city
            capitalized_city = cities_in_country[cleaned_city][1]
            # capitalize the country name
            capitalize_country = _CITY_RESOURCES['country_to_normalized_country_map'][country_code]
            candidates.append((capitalized_city, capitalize_country, 1.0))
            not_found = False

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    if not_found:
        for country_code in country_codes:
            cities_in_country = _CITY_RESOURCES['cities_per_country_code_map'][country_code]

            # Provide the input that find_closest_string expects to see
            city_to_city_name = dict()
            city_country = dict()
            for city_name, city_value in cities_in_country.items():
                city_to_city_name[city_name] = city_value[1]
                city_country[city_name] = city_value[0]

            city_match = find_closest_string(cleaned_city, city_country)

            if city_match:
                best_matches, score = city_match
                # capitalize the city name
                best_matches = [city_to_city_name[best_match] for best_match in best_matches]
                capitalize_country = _CITY_RESOURCES['country_to_normalized_country_map'][country_code]
                for best_match in best_matches:
                    candidates.append((best_match, capitalize_country, score))

    # remove duplicates such as San Jose(US and Porto Rico). Both of them returns ('San Jose', 'United States', 1.0)
    candidates = list(set(candidates))
    return sorted(candidates, key=lambda x: x[-1], reverse=True)


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
                                      .remove_suffixes({' si', ' Si', ' ri', ' Ri', ' dong', ' Dong'})  # Set of formal city suffixes
                                      .tokenize()
                                      .remove_stop_words({'der', 'do', 'e', 'le', 'im', 'mail'}, case_sensitive=True)
                                      .lowercase(on_tokens=True)
                                      .filter_tokens()
                                      .sub_tokens(lambda token: _GEO_TOKEN_MAP.get(token, token))
                                      .remove_stop_words({'a', 'an', 'and', 'cedex', 'da', 'di'
                                                          'email', 'of', 'the'})
                                      .join())


def _clean_geo_string(string: str) -> str:
    """
    Cleans a strings with geographical information (e.g., countries/states/cities).

    :param string: Input string to clean.
    :return: Cleaned string.
    """
    return _GEO_STRING_SCRUBBER.transform(string)


# Same cleaning is used for countries, states and cities
clean_country = clean_state = clean_city = _clean_geo_string


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

    # Get a map of cleaned country name to capitalized country name
    resources['cleaned_to_capitilized'] = {clean_country(country): capitalize_geo_string(country)
                                           for country in read_resource_file(__file__, 'resources/countries.txt')}

    # Read in a map of common country name replacements
    replacements_file = (line.split(", ") for line in read_resource_file(__file__, 'resources/country_map.txt'))
    resources['replacements'] = {clean_country(country): clean_country(canonical_country)
                                 for country, canonical_country in replacements_file}

    # Replacement patterns additional to the other replacements (mainly filters zipcodes)
    resources['replacement_patterns'] = [(pattern, clean_country(canonical_country)) for pattern, canonical_country in
                                         ((re.compile(r'\d+[a-z]+\d+ canada [a-z]+\d+[a-z]+', re.IGNORECASE), 'canada'),
                                          (re.compile(r'\d+ russia', re.IGNORECASE), 'russia'))]

    # Generate trigrams for the cleaned countries
    resources['cleaned_trigrams'] = {cleaned_country: get_trigram_tokens(cleaned_country)
                                     for cleaned_country in resources['cleaned_to_capitilized'].keys()}

    return resources


_COUNTRY_RESOURCES = _get_country_resources()


def _get_state_resources() -> Dict[str, Dict]:
    """
    Reads and parses state resource files.

    :return: Dictionary containing resources used for state normalization.
    """
    resources = dict()

    # Read in a map of states per country. For some states the state code is added. States and/or state codes are not
    # always unique. We don't remove stop words when we're dealing with state codes.
    resources['state_country_map'] = defaultdict(set)
    state_country_file = (line.split(", ") for line in read_resource_file(__file__, 'resources/states_per_country.txt'))
    for *state_list, canonical_country in state_country_file:
        for _state in state_list:
            resources['state_country_map'][clean_state(_state)].add((capitalize_geo_string(state_list[0]),
                                                                     clean_country(canonical_country)))

    # Generate trigrams for the cleaned states
    resources['cleaned_trigrams'] = {cleaned_state: get_trigram_tokens(cleaned_state)
                                     for cleaned_state in resources['state_country_map'].keys()}

    return resources


_STATE_RESOURCES = _get_state_resources()


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


def add_city_resources(countries: Optional[Set] = None, progress_bar: bool = False) -> None:
    """
    Read and parse city resources for new countries added to restrict_countries_or_code

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

        cities = read_resource_file(__file__, f"resources/{country_code}.txt")
        _CITY_RESOURCES["cities_per_country_code_map"][country_code] = dict()
        for city_list in cities:
            # A single line can have multiple alternative spellings of the same city. The first spelling is the
            # canonical one and all versions will point to that
            city_list = city_list.split(", ")
            canonical_city_name = city_list[0]
            for city in city_list:
                cleaned_city = clean_city(city)
                #sometimes clean_city removes the whole string
                if not cleaned_city:
                    continue
                _CITY_RESOURCES["cities_per_country_code_map"][country_code][cleaned_city] = (
                    get_trigram_tokens(cleaned_city), canonical_city_name
                )
