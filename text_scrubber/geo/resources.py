import re
from typing import Any, Dict, Callable, Generator, Optional, Set

from tqdm.auto import tqdm

from text_scrubber.io import read_resource_file, read_resource_json_file
from text_scrubber.geo.clean import clean_country, clean_region, clean_city
from text_scrubber.geo.string_distance_levenshtein import optimize_levenshtein_strings
from text_scrubber.geo.string_distance_trigrams import get_trigram_tokens, optimize_trigram_tokens


_COUNTRY_RESOURCES = dict()
_REGION_RESOURCES = {'regions_per_country_code_map': dict()}
_CITY_RESOURCES = {'cities_per_country_code_map': dict()}


def add_country_resources():
    """
    Reads and parses country resource files
    """
    global _COUNTRY_RESOURCES
    resources = _COUNTRY_RESOURCES

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

    # Replacement patterns additional to the other replacements (mainly filters zipcodes)
    resources['replacement_patterns'] = [(pattern, clean_country(canonical_country)) for pattern, canonical_country in
                                         ((re.compile(r'\d+[a-z]+\d+ canada [a-z]+\d+[a-z]+', re.IGNORECASE), 'canada'),
                                          (re.compile(r'\d+ russia', re.IGNORECASE), 'russia'))]

    # Get a map of cleaned country name and country code to canonical country name, and generate trigrams
    resources['countries'] = {'canonical_names': [],
                              'cleaned_location_map': dict(),
                              'levenshtein': dict(),
                              'trigrams': dict()}
    for canonical_country, country_codes in resources['normalized_country_to_country_codes_map'].items():
        # Add country name
        canonical_name_idx = len(resources['countries']['canonical_names'])
        cleaned_country = clean_country(canonical_country)
        resources['countries']['canonical_names'].append(canonical_country)
        resources['countries']['cleaned_location_map'][cleaned_country] = canonical_name_idx, canonical_name_idx
        _add_cleaned_location(cleaned_country, canonical_name_idx, canonical_name_idx, resources['countries'])

        # Add corresponding country codes
        for country_code in country_codes:
            idx = len(resources['countries']['canonical_names'])
            resources['countries']['canonical_names'].append(country_code)
            resources['countries']['cleaned_location_map'][country_code.lower()] = canonical_name_idx, idx
            _add_cleaned_location(country_code.lower(), canonical_name_idx, idx, resources['countries'])

    # Add common country replacements
    for location_list in read_resource_file(__file__, 'resources/country_map.txt'):
        # A single line can have multiple alternative spellings of the same country. The first spelling is the
        # canonical one and all versions will point to that
        location_list = location_list.split(", ")
        canonical_name_idx = resources['countries']['canonical_names'].index(location_list[0])
        for location, cleaned_location in zip(location_list[1:], clean_country(location_list[1:])):
            # Sometimes the clean function removes the whole string
            if not cleaned_location:
                continue

            assert cleaned_location not in resources['countries']['cleaned_location_map'], \
                f"Location {location} already exists. Contact maintainer."

            idx = len(resources['countries']['canonical_names'])
            resources['countries']['canonical_names'].append(location)
            resources['countries']['cleaned_location_map'][cleaned_location] = canonical_name_idx, idx

            # Add to Levenshtein and trigram maps
            _add_cleaned_location(cleaned_location, canonical_name_idx, idx, resources['countries'])

    # Optimize data structure for Levenshtein and trigram similarity functions
    _optimize_resources_dict(resources['countries'])


def add_region_resources(country_codes: Optional[Set[str]] = None, progress_bar: bool = False) -> None:
    """
    Read and parse region resources for new countries

    :param country_codes: Set of country codes. If None, will add all country codes
    :param progress_bar: disable or enable progressbar. Default is no progressbar (False)
    """
    global _REGION_RESOURCES

    if country_codes is None:
        country_codes = _COUNTRY_RESOURCES['all_country_codes']

    # Load resources for each country code and update the global resources
    for country_code in tqdm(country_codes, disable=not progress_bar):

        # Skip countries that are already loaded
        if country_code in _REGION_RESOURCES['regions_per_country_code_map']:
            continue

        regions = read_resource_file(__file__, f"resources/regions_per_country/{country_code}.txt")
        _REGION_RESOURCES["regions_per_country_code_map"][country_code] = _add_location_resources(regions, clean_region)


def add_city_resources(country_codes: Optional[Set[str]] = None, progress_bar: bool = False) -> None:
    """
    Read and parse city resources for new countries

    :param country_codes: Set of country codes. If None, will add all country codes
    :param progress_bar: disable or enable progressbar. Default is no progressbar (False)
    """
    global _CITY_RESOURCES

    if country_codes is None:
        country_codes = _COUNTRY_RESOURCES['all_country_codes']

    # Load resources for each country code and update the global resources
    for country_code in tqdm(country_codes, disable=not progress_bar):

        # Skip countries that are already loaded
        if country_code in _CITY_RESOURCES['cities_per_country_code_map']:
            continue

        cities = read_resource_file(__file__, f"resources/cities_per_country/{country_code}.txt")
        _CITY_RESOURCES["cities_per_country_code_map"][country_code] = _add_location_resources(cities, clean_city)


def _add_location_resources(locations: Generator[str, None, None], clean_func: Callable) -> Dict[str, Any]:
    """
    Parse and process location data

    :param locations: Generator of location strings. A single string is a comma-separated list of alternative spellings
        of the same location. The first location is the canonical name
    :param clean_func: Clean function to apply to each location
    :return: Dictionary with processed location information
    """
    location_dict = {'canonical_names': [],
                     'cleaned_location_map': dict(),
                     'levenshtein': dict(),
                     'trigrams': dict()}
    for location_list in locations:
        # A single line can have multiple alternative spellings of the same location. The first spelling is the
        # canonical one and all versions will point to that
        location_list = location_list.split(", ")
        canonical_name_idx = len(location_dict['canonical_names'])
        for location, cleaned_location in zip(location_list, clean_func(location_list)):
            # Sometimes the clean function removes the whole string
            if not cleaned_location:
                continue

            idx = len(location_dict['canonical_names'])
            location_dict['canonical_names'].append(location)
            location_dict['cleaned_location_map'][cleaned_location] = canonical_name_idx, idx

            # Add to Levenshtein and trigram maps
            _add_cleaned_location(cleaned_location, canonical_name_idx, idx, location_dict)

    # Optimize data structure for Levenshtein and trigram similarity functions
    _optimize_resources_dict(location_dict)

    return location_dict


def _add_cleaned_location(cleaned_location: str, canonical_name_idx: int, idx: int,
                          resources_dict: Dict[str, Any]) -> None:
    """
    Add a cleaned location to the resources dict and make it ready for Levenshtein and trigram similarity functions.
    Post-processing still needs to be done after this, though.

    :param cleaned_location: cleaned location string
    :param canonical_name_idx: index corresponding to the canonical version of the location
    :param idx: index corresponding to the location name
    :param resources_dict: dictionary where to store the Levenshtein and trigram information into
    """
    # Add to Levenshtein map
    size = len(cleaned_location)
    if size not in resources_dict['levenshtein']:
        resources_dict['levenshtein'][size] = {'levenshtein_tokens': [cleaned_location],
                                               'indices': [(canonical_name_idx, idx)]}
    else:
        resources_dict['levenshtein'][size]['levenshtein_tokens'].append(cleaned_location)
        resources_dict['levenshtein'][size]['indices'].append((canonical_name_idx, idx))

    # Add to trigrams map
    trigram_tokens = get_trigram_tokens(cleaned_location)
    size = len(trigram_tokens)
    if len(trigram_tokens) not in resources_dict['trigrams']:
        resources_dict['trigrams'][size] = {'trigram_tokens': [trigram_tokens],
                                            'indices': [(canonical_name_idx, idx)]}
    else:
        resources_dict['trigrams'][size]['trigram_tokens'].append(trigram_tokens)
        resources_dict['trigrams'][size]['indices'].append((canonical_name_idx, idx))


def _optimize_resources_dict(resources_dict: Dict[str, Any]) -> None:
    """
    Optimize Levenshtein and trigram data structures

    :param resources_dict: dictionary where to get and store the optimized Levenshtein and trigram information into
    """
    # Optimize data structure for Levenshtein
    for n_chars, locations_dict_part in resources_dict['levenshtein'].items():
        char_matrix = optimize_levenshtein_strings(locations_dict_part['levenshtein_tokens'])
        locations_dict_part['char_matrix'] = char_matrix

    # Optimize data structure for trigrams
    for n_trigrams, locations_dict_part in resources_dict['trigrams'].items():
        trigram_matrix = optimize_trigram_tokens(locations_dict_part['trigram_tokens'])
        locations_dict_part['trigram_tokens'] = trigram_matrix


add_country_resources()
