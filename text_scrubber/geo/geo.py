import re
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm
from typing import List, Tuple, Dict, Optional, Set, Union
import warnings

from text_scrubber import TextScrubber
from text_scrubber.io import read_resource_file, read_resource_pickle_file
from text_scrubber.string_distance import find_closest_string, get_trigram_tokens, pattern_match


def normalize_country(country: str) -> List[Union[Tuple[str, float], Tuple[str]]]:
    """
    Cleans up a country by string cleaning and performs some basic country lookups to get the canonical name.

    :param country: Country string to clean.
    :return: List of country candidates in canonical form. Optionally accompanied with match scores.
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


def normalize_state(state: str) -> List[Union[Tuple[str, str, float], Tuple[str, str]]]:
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


def normalize_city(
    city: str, restrict_countries_or_code: Optional[Set] = None
) -> List[Tuple[str, str, float]]:
    """
    Cleans up a city by string cleaning and performs some basic city lookups to get the canonical name.

    :param restrict_countries_or_code: countries code or their name to restrict search space
    :param city: City name.
    :return: List of (city, country) candidates in canonical form.
    """
    # Clean city
    cleaned_city = clean_city(city)

    # restrict the countries search
    add_city_resources(restrict_countries_or_code)
    if (_CITY_RESOURCES == {}):
        warnings.warn("No valid country name to search for city!")
        return []
    restricted_city_resources = {"country_code_to_country":dict(), "cities_per_country_map": dict()}

    # uppercase all items to make them case-insensitive
    restrict_countries_or_code = {item.lower() for item in restrict_countries_or_code}
    if restrict_countries_or_code is not None:
        for code, country in _CITY_RESOURCES["country_code_to_country"].items():
            if code.lower() in restrict_countries_or_code or country.lower() in restrict_countries_or_code:
                restricted_city_resources["country_code_to_country"][code] = country
        for code, country in restricted_city_resources["country_code_to_country"].items():
            restricted_city_resources["cities_per_country_map"][code.lower()] = \
            _CITY_RESOURCES["cities_per_country_map"][code.lower()]
            restricted_city_resources["cities_per_country_map"][country.lower()] = \
            _CITY_RESOURCES["cities_per_country_map"][country.lower()]


    # Check if city is part of the known cities list
    candidates = []
    not_found = True
    for country, cities_in_country in restricted_city_resources["cities_per_country_map"].items():
        # This condition prevent from searching again in country codes
        if len(country) > 2:
            # all_cities = set(cities_in_country.keys())
            if cleaned_city in cities_in_country:
                # return the exact name of the city
                capitalize_city = cities_in_country[cleaned_city][1]
                # capitalize the country name
                capitalize_country = capitalize_geo_string(country)
                candidates.append(
                    (capitalize_city, capitalize_country, 1.0)
                )
                not_found = False

    # Check if we can find a close match (using default threshold of 0.8 (magic number))
    if not_found:
        for country, cities_in_country in restricted_city_resources["cities_per_country_map"].items():
            # This condition prevent from searching again in country codes
            if len(country) > 2:
                # provide the input that find_closest_string expect to see
                city2cityname = dict()
                city_country = dict()
                for cityname, city_value in cities_in_country.items():
                    city2cityname[cityname] = city_value[1]
                    city_country[cityname] = city_value[0]
                city_match = find_closest_string(cleaned_city, city_country)
                if city_match:
                    best_matches, score = city_match
                    # capitalize the city name
                    best_matches = [city2cityname[best_match] for best_match in best_matches]
                    capitalize_country = capitalize_geo_string(country)
                    for best_match in best_matches:
                        candidates.append(
                            (best_match, capitalize_country, score)
                        )

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



def _get_city_resources(restrict_countries_code: Optional[Set] = None, disable_progressbar: bool = True) -> Dict[str, Dict]:
    """
    Reads and parses city resource files.

    :param restrict_countries_code: Restrict the search space to this set of countries. If no country code is inserted,
    the function will load all countries.
    :param disable_progressbar: disable or enable progressbar. Default is no progressbar (True)
    :return: Dictionary containing resources used for city normalization.
    """
    resources = dict()

    # Load map of country codes to countries
    country_code_to_country = read_resource_pickle_file(__file__, "resources/country_code_map.p3")

    # filter dictionary of countries
    if restrict_countries_code is not None:
        country_code_to_country = {
            key: value for key, value in country_code_to_country.items() if key in restrict_countries_code
        }
    resources["country_code_to_country"] = country_code_to_country

    # Get a map of cleaned city name to (city name, cleaned country). City names are not always unique. Some
    # countries here first have to be normalized
    resources["cities_per_country_map"] = defaultdict(dict)
    for country_code, country in tqdm(country_code_to_country.items(), disable=disable_progressbar):
        cleaned_country = clean_country(country)
        cities = read_resource_file(__file__, f"resources/{country_code}.txt")
        for city in cities:
            cleaned_city = clean_city(city)
            resources["cities_per_country_map"][cleaned_country][cleaned_city] = [get_trigram_tokens(cleaned_city), city]

        # Users can also supply a country code to get the country code :)
        resources["cities_per_country_map"][country_code.lower()] = resources["cities_per_country_map"][cleaned_country]

    return resources


_CITY_RESOURCES = dict()

def add_city_resources(restrict_countries_or_code: Optional[Set] = None):
    '''
    Read and parse city resources for new countries added to restrict_countries_or_code

    :param restrict_countries_or_code: Only load the list of countries or country codes provided
    :return:
    '''
    country_code_to_country = read_resource_pickle_file(__file__, "resources/country_code_map.p3")
    global _CITY_RESOURCES

    restrict_countries_code = None
    if restrict_countries_or_code is not None:
        # normalizing the names before adding their resources
        temp_set = set()
        for item in restrict_countries_or_code:
            if len(item)>2: # make sure it is not a country code
                normalized_country = normalize_country(item)
                if len(normalized_country):
                    temp_set.add(normalized_country[0][0])
                else:
                    temp_set.add(item.upper())
            else:
                temp_set.add(item.upper())
        restrict_countries_or_code = temp_set

        # uppercase all items to make them case-insensitive
        restrict_countries_or_code = {item.upper() for item in restrict_countries_or_code}
        restrict_countries_code = set()
        for code, country in country_code_to_country.items():
            if code in restrict_countries_or_code:
                restrict_countries_code.add(code)
                restrict_countries_or_code.remove(code)

            if country.upper() in restrict_countries_or_code:
                restrict_countries_code.add(code)
                restrict_countries_or_code.remove(country.upper())

        if len(restrict_countries_or_code) != 0:
            warnings.warn(f"The following strings are not country names or codes\n {restrict_countries_or_code}")

        # only call _get_city_resources for countries that are not already inside _CITY_RESOURCES
        if _CITY_RESOURCES != {}:
            restrict_countries_code = [code for code in restrict_countries_code if code not in _CITY_RESOURCES["country_code_to_country"].keys()]

        # If someone called the function on the same countries again it will pass this steps
        if len(restrict_countries_code) != 0:
            updates_city_resources = _get_city_resources(restrict_countries_code)

            # update or write the _CITY_RESOURCES
            if _CITY_RESOURCES != {}:
                _CITY_RESOURCES["country_code_to_country"].update(updates_city_resources["country_code_to_country"])
                _CITY_RESOURCES["cities_per_country_map"].update(updates_city_resources["cities_per_country_map"])
            else:
                _CITY_RESOURCES = updates_city_resources

    else:
        _CITY_RESOURCES = _get_city_resources()


st = datetime.now()
