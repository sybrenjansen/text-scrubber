import unittest

from text_scrubber.geo import (_clean_geo_string, capitalize_geo_string, normalize_country, normalize_state,
                               normalize_city)


class NormalizeCountryTest(unittest.TestCase):

    def test_part_of_known_countries(self):
        """
        Test input that is part of the standard countries map
        """
        test_countries = [
            ('Afghanistan', ['Afghanistan']),
            ('BAHAMAS', ['Bahamas']),
            ('Cambodia', ['Cambodia']),
            ('Denmark', ['Denmark']),
            ('east timor', ['East Timor']),
            ('Fiji', ['Fiji']),
            ('Gabon', ['Gabon']),
            ('HaITI', ['Haiti']),
            ('Iceland', ['Iceland']),
            ('Jamaica', ['Jamaica']),
            ('Kazakhstan', ['Kazakhstan']),
            ('Laos', ['Laos']),
            ('Macedonia', ['Macedonia']),
            ('Namibia', ['Namibia']),
            ('Oman', ['Oman']),
            ('Pakistan', ['Pakistan']),
            ('Qatar', ['Qatar']),
            ('Romania', ['Romania']),
            ('Vincent Saint', ['Saint Vincent']),
            ('Tajikistan', ['Tajikistan']),
            ('Uganda', ['Uganda']),
            ('Vanuatu', ['Vanuatu']),
            ('Yemen', ['Yemen']),
            ('Zambia', ['Zambia']),
        ]
        for original, expected in test_countries:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_country(original), expected)

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_country('*'), [])
        self.assertEqual(normalize_country('fooBar'), [])
        self.assertEqual(normalize_country('New South Wales'), [])
        self.assertEqual(normalize_country('Paris'), [])

    def test_common_country_replacements(self):
        """
        Common country replacements should be picked up
        """
        test_countries = [
            ('republica argentina', ['Argentina']),
            ('kingdom of Bahrain', ['Bahrain']),
            ('Peoples republic of China', ['China']),
            ('FR', ['France']),
            ('Allemagne', ['Germany']),
            ('KASSR', ['Kazakhstan']),
            ('cook Islands', ['New Zealand'])
        ]
        for original, expected in test_countries:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_country(original), expected)

    def test_close_match(self):
        """
        Close matches to the standard countries map should yield the correct country
        """
        test_countries = [
            ('Belgum', ['Belgium']),
            ('Jamayca', ['Jamaica']),
            ('mecico', ['Mexico']),
            ('saint Nevis and Kitties', ['Saint Kitts and Nevis'])
        ]
        for original, expected in test_countries:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_country(original), expected)

    def test_not_close_enough_match(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_countries = [
            'Beglumi',
            'Janaayka',
            'mechicoooo',
            'st Nefviecs or Kittieeeees'
        ]
        for original in test_countries:
            with self.subTest(original=original):
                self.assertEqual(normalize_country(original), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the standard countries map should yield all correct countries
        """
        test_countries = [
            ('Ira', ['Iran', 'Iraq']),
            ('oth korea', ['North Korea', 'South Korea']),
            ('Slovia', ['Slovakia', 'Slovenia'])
        ]
        for original, expected in test_countries:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_country(original), expected)

    def test_country_pattern_match(self):
        """
        When the input string follows a certain country pattern it should yield the correct country
        """
        test_countries = [
            ('5A5 canada B34C', ['Canada']),
            ('2F2 Canada C3Q', ['Canada']),
            ('234522 Russia', ['Russia']),
            ('998833 russia', ['Russia'])
        ]
        for original, expected in test_countries:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_country(original), expected)


class NormalizeStateTest(unittest.TestCase):

    def test_part_of_known_states(self):
        """
        Test input that is part of the states map
        """
        test_states = [
            ('Queensland', [('Queensland', 'Australia')]),
            ('QLd', [('Queensland', 'Australia')]),
            ('Rio de Janeiro', [('Rio De Janeiro', 'Brazil')]),
            ('ON', [('Ontario', 'Canada')]),
            ('okinaWA', [('Okinawa', 'Japan')]),
            ('Georgia', [('Georgia', 'United States')]),
            ('NY', [('New York', 'United States')]),
        ]
        for original, expected in test_states:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_state(original), expected)

    def test_multiple_matches(self):
        """
        Test input that is part of the states map that return multiple matches
        """
        test_states = [
            ('WA', [('Washington', 'United States'), ('Western Australia', 'Australia')]),
            ('AR', [('Arkansas', 'United States'), ('Arunachal Pradesh', 'India')]),
            ('nl', [('Nagaland', 'India'), ('Newfoundland and Labrador', 'Canada')])
        ]
        for original, expected in test_states:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_state(original), expected)

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_state('*'), [])
        self.assertEqual(normalize_state('fooBar'), [])
        self.assertEqual(normalize_state('Brazil'), [])
        self.assertEqual(normalize_state('Paris'), [])

    def test_close_match(self):
        """
        Close matches to the states map should yield the correct state
        """
        test_states = [
            ('Ilinios', [('Illinois', 'United States')]),
            ('Saytama', [('Saitama', 'Japan')]),
            ('kashmir and jannu', [('Jammu and Kashmir', 'India')]),
            ('King Kong', [('Hong Kong', 'China')])
        ]
        for original, expected in test_states:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_state(original), expected)

    def test_not_close_enough_match(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_states = [
            'Lillyniose',
            'Syiatammma',
            'Cashmere and Jammu',
            'Diddy Kong'
        ]
        for original in test_states:
            with self.subTest(original=original):
                self.assertEqual(normalize_state(original), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the states map should yield all correct states
        """
        test_states = [
            ('Jiang', [('Jiangsu', 'China'), ('Jiangxi', 'China')]),
            ('oshima', [('Hiroshima', 'Japan'), ('Kagoshima', 'Japan'), ('Tokushima', 'Japan')]),
            ('VWA', [('Virginia', 'United States'), ('Washington', 'United States'),
                     ('Western Australia', 'Australia')])
        ]
        for original, expected in test_states:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_state(original), expected)


class NormalizeCityTest(unittest.TestCase):

    def test_part_of_known_cities(self):
        """
        Test input that is part of the cities map
        """
        test_cities = [
            ('Boolaroo', [('Boolaroo', 'Australia')]),
            ('Leibnitz', [('Leibnitz', 'Austria')]),
            ('ivry-sur-seine', [('Ivry-sur-seine', 'France')]),
            ('Rivoli', [('Rivoli', 'Italy')]),
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original), expected)

    def test_multiple_matches(self):
        """
        Test input that is part of the cities map that return multiple matches
        """
        test_cities = [
            ('woodstock',  [('Woodstock', 'Australia'), ('Woodstock', 'Canada'),
                            ('Woodstock', 'United Kingdom'), ('Woodstock', 'United States')]),
            ('heidelberg', [('Heidelberg', 'Australia'), ('Heidelberg', 'Germany'),
                            ('Heidelberg', 'South Africa'), ('Heidelberg', 'United States')]),
            ('San Jose', [('San Jose', 'Argentina'), ('San Jose', 'Philippines'), ('San Jose', 'Spain'),
                          ('San Jose', 'United States'), ('San José', 'Costa Rica')])
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original), expected)

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_city('*'), [])
        self.assertEqual(normalize_city('fooBar'), [])
        self.assertEqual(normalize_city('United States'), [])

    def test_removal_of_city_suffixes(self):
        """
        Suffixes ' si', ' ri' and ' dong' should be removed before matching
        """
        test_cities = [
            ('wonju si', [('Wonju', 'South Korea')]),
            ('Gimhae-Si', [('Gimhae', 'South Korea')]),
            ('Zhaoqing dong', [('Zhaoqing', 'China')]),
            ('Asan ri', [('Asan', 'South Korea')])
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original), expected)

    def test_close_match(self):
        """
        Close matches to the cities map should yield the correct city
        """
        test_cities = [
            ('Texas', [('Texas City', 'United States')]),
            ('Kiyoto', [('Kyoto', 'Japan')]),
            ('Napholi', [('Napoli', 'Italy')]),
            ('leeeR', [('Leer', 'Germany')])
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original), expected)

    def test_not_close_enough_match(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_cities = [
            'Texaas',
            'Kiyootoo',
            'Napolilyla',
            'Leieierr'
        ]
        for original in test_cities:
            with self.subTest(original=original):
                self.assertEqual(normalize_city(original), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the states map should yield all correct states
        """
        test_cities = [
            ('Pari', [('Parai', 'Brazil'), ('Paris', 'Canada'), ('Paris', 'France'), ('Paris', 'United States'),
                      ('Parit', 'Malaysia'), ('Pariz', 'Czech Republic')]),
            ('canada', [('Canadian', 'Australia'), ('Canadian', 'United States'), ('Chantada', 'Spain')]),
            ('KIWI', [('Kirwin', 'United States'), ('Kiwity', 'Poland')])
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original), expected)


class CleanGeoStringTest(unittest.TestCase):

    def test_lowercase(self):
        """
        String should be lowercased
        """
        test_input = [
            ('ITALY', 'italy'),
            ('HELLO WorLD', 'hello world'),
            ('Diego San', 'diego san')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_to_ascii(self):
        """
        Unicode characters should be translated to closest ascii equivalent
        """
        test_input = [
            ('北京', 'bei jing'),
            ('durrës', 'durres'),
            ('béjaïa', 'bejaia'),
            ('płońsk', 'plonsk')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_remove_digits(self):
        """
        Digits should be removed
        """
        test_input = [
            ('paris 1', 'paris'),
            ('1234 amsterdam', 'amsterdam'),
            ('sz4b0lcsv3r3sm4rt', 'szblcsvrsmrt')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_remove_punctuation(self):
        """
        Some punctuation will be completely removed
        """
        test_input = [
            ('text_with{a}lot.of"punctuation!@#', 'textwithalotofpunctuation')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_substitute_punctuation(self):
        """
        Some punctuation will be replaced by a space
        """
        test_input = [
            ('neustadt/westerwald', 'neustadt westerwald'),
            ('golub-dobrzyn', 'golub dobrzyn'),
            ('some,text', 'some text'),
            ('fort-de-france', 'fort de france')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_strip_suffixes(self):
        """
        Set of formal city suffixes should be removed. When it's not a suffix it should remain there
        """
        test_input = [
            ('wonju si', 'wonju'),
            ('Gimhae-Si', 'gimhae'),
            ('Zhaoqing dong', 'zhaoqing'),
            ('Asan ri', 'asan'),
            ('dong ri si text', 'dong ri si text')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_substitute_geo_tokens(self):
        """
        Some abbreviations should be replaced by the full name
        """
        test_input = [
            ('cent afr rep', 'central african republic'),
            ('brit isl', 'brittish islands'),
            ('dem republ', 'democratic republic'),
            ('equat guinea', 'equatorial guinea'),
            ('isla bonita', 'islands bonita'),
            ('is island', 'islands islands'),
            ('monteneg', 'montenegro'),
            ('neth', 'netherlands'),
            ('republik deutschland', 'republic deutschland'),
            ('sint maarten', 'saint maarten'),
            ('st vincent', 'saint vincent')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)

    def test_remove_stop_words(self):
        """
        Some stop words should be removed
        """
        test_input = [
            ('italy e-mail', 'italy'),
            ('trinidad and tobago', 'trinidad tobago'),
            ('federated states of micronesia', 'federated states micronesia')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(_clean_geo_string(original), expected)


class CapitalizeGeoStringTest(unittest.TestCase):

    def test_capitalize(self):
        """
        All tokens should be capitalized
        """
        test_input = [
            ("it doesn't have to be a country", "It Doesn't Have To Be A Country"),
            ('solomon Islands', 'Solomon Islands'),
            ('united Arab emirates', 'United Arab Emirates')
        ]
        for original, expected in test_input:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(capitalize_geo_string(original), expected)

    def test_exlude_and_of(self):
        """
        Tokens 'and' and 'of' should not be capitalized
        """
        test_input = [
            ('trinidad and tobago', 'Trinidad and Tobago'),
            ('united states of america', 'United States of America')
        ]
        for original, expected in test_input:
            self.assertEqual(capitalize_geo_string(original), expected)
