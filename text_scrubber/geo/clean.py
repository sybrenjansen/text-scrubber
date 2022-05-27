from typing import List, Union

from text_scrubber import TextScrubber

# Some common token replacements
_GEO_TOKEN_MAP = {'afr': 'african',
                  'brit': 'brittish',
                  'cent': 'central',
                  'dem': 'democratic',
                  'democratique': 'democratic',
                  'demokratische': 'democratic',
                  'equat': 'equatorial',
                  'fed': 'federal',
                  'is': 'islands',
                  'isl': 'islands',
                  'isla': 'islands',
                  'island': 'islands',
                  'monteneg': 'montenegro',
                  'neth': 'netherlands',
                  'rep': 'republic',
                  'republ': 'republic',
                  'republik': 'republic',
                  'republique': 'republic',
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
