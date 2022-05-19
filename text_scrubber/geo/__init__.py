import pyximport

# Let Cython files compile on the fly. This needs to happen before the other imports, as they're dependent on it
pyximport.install(inplace=True)

from text_scrubber.geo.clean import clean_city, clean_country, clean_region
from text_scrubber.geo.find_in_string import find_city_in_string, find_country_in_string, find_region_in_string
from text_scrubber.geo.normalize import (normalize_city, normalize_country, normalize_country_to_country_codes,
                                         normalize_region)
from text_scrubber.geo.resources import add_city_resources, add_region_resources
