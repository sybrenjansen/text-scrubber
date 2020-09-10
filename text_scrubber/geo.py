import re
from collections import defaultdict
from typing import List, Tuple, Dict

from text_scrubber import TextScrubber
from text_scrubber.io import read_resource_file
from text_scrubber.string_distance import find_closest_string, get_trigram_tokens, pattern_match


def normalize_country(country: str) -> List[str]:
    """
    Cleans up a country by string cleaning and performs some basic country lookups to get the canonical name.

    :param country: Country string to clean.
    :return: List of country candidates in canonical form.
    """
    # Clean country
    cleaned_country = clean_country(country)

    # When have no input after cleaning it should return the original
    if not cleaned_country:
        return []

    # Check if country is part of the known countries list
    if cleaned_country in _COUNTRY_RESOURCES['cleaned_to_capitilized']:
        return [_COUNTRY_RESOURCES['cleaned_to_capitilized'][cleaned_country]]

    # There's a number of known expansions/translations which can be applied. Check if we can find anything with that
    if cleaned_country in _COUNTRY_RESOURCES['replacements']:
        return [_COUNTRY_RESOURCES['cleaned_to_capitilized'][_COUNTRY_RESOURCES['replacements'][cleaned_country]]]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    country_match = find_closest_string(cleaned_country, _COUNTRY_RESOURCES['cleaned_trigrams'])
    if country_match:
        best_matches, _ = country_match
        return [_COUNTRY_RESOURCES['cleaned_to_capitilized'][country] for country in best_matches]

    # Check if the country follows a certain country pattern
    known_country = pattern_match(country, _COUNTRY_RESOURCES['replacement_patterns'])
    if known_country:
        return [_COUNTRY_RESOURCES['cleaned_to_capitilized'][known_country]]

    # No match found
    return []


def normalize_state(state: str) -> List[Tuple[str, str]]:
    """
    Cleans up a state by string cleaning and performs some basic state lookups to get the canonical name.

    :param state: State name or code.
    :return: List of (state, country) candidates in canonical form.
    """
    # Clean state
    cleaned_state = clean_state(state)

    # Check if state is part of the known states list
    if cleaned_state in _STATE_RESOURCES['state_country_map']:
        candidates = _STATE_RESOURCES['state_country_map'][cleaned_state]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    else:
        state_match = find_closest_string(cleaned_state, _STATE_RESOURCES['cleaned_trigrams'])
        if state_match:
            best_matches, _ = state_match
            candidates = [candidate for state in best_matches
                          for candidate in _STATE_RESOURCES['state_country_map'][state]]
        else:
            # No match found
            candidates = []

    # Return canonical form
    return sorted((state, _COUNTRY_RESOURCES['cleaned_to_capitilized'][country]) for state, country in candidates)


def normalize_city(city: str) -> List[Tuple[str, str]]:
    """
    Cleans up a city by string cleaning and performs some basic city lookups to get the canonical name.

    :param city: City name.
    :return: List of (city, country) candidates in canonical form.
    """
    # Clean city
    cleaned_city = clean_city(city)

    # Check if city is part of the known cities list
    if cleaned_city in _CITY_RESOURCES['city_country_map']:
        candidates = _CITY_RESOURCES['city_country_map'][cleaned_city]

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    else:
        city_match = find_closest_string(cleaned_city, _CITY_RESOURCES['cleaned_trigrams'])
        if city_match:
            best_matches, _ = city_match
            candidates = [candidate for city in best_matches for candidate in _CITY_RESOURCES['city_country_map'][city]]
        else:
            # No match found
            candidates = []

    # Return canonical form
    return sorted((city, _COUNTRY_RESOURCES['cleaned_to_capitilized'][country]) for city, country in candidates)


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
                  'st': 'saint'}

# We define the scrubber once so the regex objects will be compiled only once
_GEO_STRING_SCRUBBER = (TextScrubber().to_ascii()
                                      .lowercase()
                                      .remove_digits()
                                      .sub(r'-|/|&|,', ' ')
                                      .remove_punctuation()
                                      .remove_suffixes({' si', ' ri', ' dong'})  # Set of formal city suffixes
                                      .tokenize()
                                      .filter_tokens()
                                      .sub_tokens(lambda token: _GEO_TOKEN_MAP.get(token, token))
                                      .remove_stop_words({'a', 'an', 'and', 'cedex', 'da', 'der', 'di', 'do', 'e',
                                                          'email', 'im', 'le', 'mail', 'of', 'the'})
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
                                         ((re.compile(r'\d[a-z]\d canada [a-z]\d[a-z]', re.IGNORECASE), 'canada'),
                                          (re.compile(r'\d{6} russia', re.IGNORECASE), 'russia'))]

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


def _get_city_resources() -> Dict[str, Dict]:
    """
    Reads and parses city resource files.

    :return: Dictionary containing resources used for city normalization.
    """
    resources = dict()

    # Get a map of cleaned city name to (capitalized city name, cleaned country). City names are not always unique. Some
    # countries here first have to be normalized
    resources['city_country_map'] = defaultdict(set)
    city_country_file = (line.split(", ") for line in read_resource_file(__file__, 'resources/cities_per_country.txt'))
    for canonical_country, city in city_country_file:
        cleaned_country = clean_country(canonical_country)
        if cleaned_country not in _COUNTRY_RESOURCES['cleaned_to_capitilized']:
            cleaned_country = [clean_country(country) for country in normalize_country(canonical_country)]
        else:
            cleaned_country = [cleaned_country]
        for country in cleaned_country:
            resources['city_country_map'][clean_city(city)].add((capitalize_geo_string(city), country))

    # Generate trigrams for the cleaned states
    resources['cleaned_trigrams'] = {cleaned_city: get_trigram_tokens(cleaned_city)
                                     for cleaned_city in resources['city_country_map'].keys()}

    return resources


_CITY_RESOURCES = _get_city_resources()
