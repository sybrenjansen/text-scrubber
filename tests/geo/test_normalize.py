import unittest
from unittest.mock import patch

from text_scrubber.geo.normalize import (capitalize_geo_string, Location, normalize_city, normalize_country,
                                         normalize_region)
from text_scrubber.geo.string_distance import find_closest_string


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
                self.assertEqual(normalize_country(original), [Location(c, c, None, 1.0) for c in expected])

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
            ('republica argentina', [('Argentina', 'Republica Argentina')]),
            ('kingdom of Bahrain', [('Bahrain', 'Kingdom of Bahrain')]),
            ('Peoples republic of China', [('China', 'Peoples Republic of China')]),
            ('FR', [('France', 'FR')]),
            ('Allemagne', [('Germany', 'Allemagne')]),
            ('KASSR', [('Kazakhstan', 'KASSR')]),
            ('cook Islands', [('New Zealand', 'Cook Islands')])
        ]
        for original, expected in test_countries:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_country(original), [Location(canonical_name, matched_name, None, 1.0)
                                                               for canonical_name, matched_name in expected])

    def test_close_match(self):
        """
        Close matches to the standard countries map should yield the correct country
        """
        test_countries = [
            ('Belgum', ['Belgium'], [0.923]),
            ('Jamayca', ['Jamaica'], [0.857]),
            ('mecico', ['Mexico'], [0.833]),
            ('saint Nevis and Kitties', ['Saint Kitts and Nevis'], [0.75])
        ]
        for original, expected_countries, expected_scores in test_countries:
            with self.subTest(original=original, expected_countries=expected_countries,
                              expected_scores=expected_scores):
                for match, expected_country, expected_score in zip(
                        normalize_country(original), expected_countries, expected_scores
                ):
                    self.assertEqual(match.canonical_name, expected_country)
                    self.assertEqual(match.matched_name, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

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
            ('Ira', ['Iran', 'Iraq'], [0.857, 0.857]),
            ('oth korea', ['North Korea', 'South Korea'], [0.9, 0.9]),
            ('Slovia', ['Slovakia', 'Slovenia'], [0.857, 0.857])
        ]
        for original, expected_countries, expected_scores in test_countries:
            with self.subTest(original=original, expected_countries=expected_countries,
                              expected_scores=expected_scores):
                for match, expected_country, expected_score in zip(
                        normalize_country(original), expected_countries, expected_scores
                ):
                    self.assertEqual(match.canonical_name, expected_country)
                    self.assertEqual(match.matched_name, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_country_pattern_match(self):
        """
        When the input string follows a certain country pattern it should yield the correct country
        """
        test_countries = [
            ('5A5 canada B34C', ['Canada'], [1.0]),
            ('2F2 Canada C3Q', ['Canada'], [1.0]),
            ('234522 Russia', ['Russia'], [1.0]),
            ('998833 russia', ['Russia'], [1.0])
        ]
        for original, expected_countries, expected_scores in test_countries:
            with self.subTest(original=original, expected_countries=expected_countries,
                              expected_scores=expected_scores):
                for match, expected_country, expected_score in zip(
                        normalize_country(original), expected_countries, expected_scores
                ):
                    self.assertEqual(match.canonical_name, expected_country)
                    self.assertEqual(match.matched_name, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_thresholds_are_passed(self):
        """
        Test if the thresholds are correctly passed on to the find_closest_string function
        """
        for min_score_levenshtein, min_score_trigram in [(0.8, 0.5), (0.5, 0.8), (0.1, 0.1)]:
            with self.subTest(min_score_levenshtein=min_score_levenshtein, min_score_trigram=min_score_trigram), \
                    patch('text_scrubber.geo.normalize.find_closest_string', side_effect=find_closest_string) as p:
                normalize_country('a country name', min_score_levenshtein, min_score_trigram)
                self.assertEqual(p.call_args[0][-2:], (min_score_levenshtein, min_score_trigram))


class NormalizeRegionTest(unittest.TestCase):

    def test_part_of_known_regions(self):
        """
        Test input that is part of the regions map
        """
        test_regions = [
            ('Queensland', [('State of Queensland', 'Queensland', 'Australia')]),
            ('QLd', [('State of Queensland', 'QLD', 'Australia')]),
            ('Rio de Janeiro', [('Rio De Janeiro', 'Rio De Janeiro', 'Brazil')]),
            ('ON', [('Ontario', 'ON', 'Canada')]),
            ('okinaWA', [('Okinawa', 'Okinawa', 'Japan')]),
            ('Georgia', [('Georgia', 'Georgia', 'United States')]),
            ('NY', [('New York', 'NY', 'United States')]),
        ]
        for original, expected in test_regions:
            country_set = {country for _, _, country in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_region(original, restrict_countries=country_set),
                                 [Location(canonical_name, matched_name, country, 1.0)
                                  for canonical_name, matched_name, country in expected])

    def test_multiple_matches(self):
        """
        Test input that is part of the regions map that return multiple matches
        """
        test_regions = [
            ('WA', [('State of Western Australia', 'WA', 'Australia'), ('Washington', 'WA', 'United States')]),
            ('AR', [('Arkansas', 'AR', 'United States'), ('Ār', 'Ār', 'India')]),
            ('nl', [('Newfoundland and Labrador', 'NL', 'Canada'), ('State of Nāgāland', 'NL', 'India')])
        ]
        for original, expected in test_regions:
            country_set = {country for _, _, country in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_region(original, restrict_countries=country_set),
                                 [Location(canonical_name, matched_name, country, 1.0)
                                  for canonical_name, matched_name, country in expected])

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_region('*', restrict_countries={'Netherlands'}), [])
        self.assertEqual(normalize_region('fooBar', restrict_countries={'Jamaica'}), [])
        self.assertEqual(normalize_region('Brazil', restrict_countries={'Australia'}), [])
        self.assertEqual(normalize_region('Paris', restrict_countries={'monaco'}), [])

    def test_close_match(self):
        """
        Close matches to the regions map should yield the correct region
        """
        test_regions = [
            ('Ilinios', [('Illinois', 'Illinois', 'United States')], [0.8]),
            ('Saytama-Ken', [('Saitama-ken', 'Saitama-ken', 'Japan')], [0.909]),
            ('kashmir and jannu', [('State of Jammu and Kashmīr', 'Jammu & Kashmir', 'India')], [0.6]),
            ('King Kong', [('Kalingkong', 'Kalingkong', 'China')], [0.842])
        ]
        for original, expected_regions, expected_scores in test_regions:
            country_set = {country for _, _, country in expected_regions}
            with self.subTest(original=original, expected_regions=expected_regions, expected_scores=expected_scores):
                for match, (expected_canonical_name, expected_matched_name, expected_country), expected_score in zip(
                        normalize_region(original, restrict_countries=country_set), expected_regions, expected_scores
                ):
                    self.assertEqual(match.canonical_name, expected_canonical_name)
                    self.assertEqual(match.matched_name, expected_matched_name)
                    self.assertEqual(match.country, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_not_close_enough_match(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_regions = [
            'Lillyniose',
            'Syiatammmmma-Ken',
            'Cashmere and Jammu',
            'Diddy Kong'
        ]
        for original in test_regions:
            with self.subTest(original=original):
                self.assertEqual(normalize_region(original,
                                                  restrict_countries={'United States', 'Japan', 'India', 'China'}), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the regions map should yield all correct regions
        """
        test_regions = [
            ('Jiangs', [('Gyangsa', 'Jiangsa', 'China', 0.923),
                        ('Jiangse', 'Jiangse', 'China', 0.923),
                        ('Jiangsi', 'Jiangsi', 'China', 0.923),
                        ('Jiangsu Sheng', 'Jiangsu', 'China', 0.923),
                        ('Jigang', 'Jigang', 'China', 0.833),
                        ('Jiyang', 'Jiyang', 'China', 0.833)]),
            ('usaka', [('Fusaka', 'Fusaka', 'Japan', 0.909),
                       ('Suzaka-shi', 'Susaka', 'Japan', 0.909),
                       ('Uesaka', 'Uesaka', 'Japan', 0.909),
                       ('Yusaka', 'Yusaka', 'Japan', 0.909),
                       ('Ōsaka', 'おうさか', 'Japan', 0.909)]),
            ('VWA', [('State of Western Australia', 'WA', 'Australia', 0.8),
                     ('Virginia', 'VA', 'United States', 0.8),
                     ('Washington', 'WA', 'United States', 0.8)])
        ]
        for original, expected_regions in test_regions:
            country_set = {country for _, _, country, _ in expected_regions}
            with self.subTest(original=original, expected_regions=expected_regions):
                for match, (expected_canonical_name, expected_matched_name, expected_country, expected_score) in zip(
                        normalize_region(original, restrict_countries=country_set), expected_regions
                ):
                    self.assertEqual(match.canonical_name, expected_canonical_name)
                    self.assertEqual(match.matched_name, expected_matched_name)
                    self.assertEqual(match.country, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_thresholds_are_passed(self):
        """
        Test if the thresholds are correctly passed on to the find_closest_string function
        """
        for min_score_levenshtein, min_score_trigram in [(0.8, 0.5), (0.5, 0.8), (0.1, 0.1)]:
            with self.subTest(min_score_levenshtein=min_score_levenshtein, min_score_trigram=min_score_trigram), \
                    patch('text_scrubber.geo.normalize.find_closest_string', side_effect=find_closest_string) as p:
                normalize_region('a region name', {'NL'}, min_score_levenshtein, min_score_trigram)
                self.assertEqual(p.call_args[0][-2:], (min_score_levenshtein, min_score_trigram))


class NormalizeCityTest(unittest.TestCase):

    def test_part_of_known_cities(self):
        """
        Test input that is part of the cities map
        """
        test_cities = [
            ("Booleroo", [("Booleroo", "Australia", 1)]),
            ("Leibnitz", [("Leibnitz", "Austria", 1)]),
            ("ivry-sur-seine", [("Ivry-sur-Seine", "France", 1)]),
            ("Birjand", [("Bīrjand", "Iran", 1)]),
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original, {"Australia", "Austria", "FR", "IR"}),
                                 [Location(city, city, country, score)
                                  for city, country, score in expected])

    def test_multiple_matches(self):
        """
        Test input that is part of the cities map that return multiple matches
        """
        test_cities = [
            (
                "woodstock",
                [
                    ("Woodstock", "Woodstock", "Australia", 1),
                    ("Woodstock", "Woodstock", "Canada", 1),
                    ("Woodstock", "Woodstock", "United Kingdom", 1),
                    ("Woodstock", "Woodstock", "United States", 1),
                ],
            ),
            (
                "heidelberg",
                [
                    ("Heidelberg", "Heidelberg", "Germany", 1),
                    ("Heidelberg", "Heidelberg", "South Africa", 1),
                    ("Heidelberg", "Heidelberg", "United States", 1)
                ],
            ),
            (
                "San Jose",
                [
                    ('San Jose Village', 'San Jose', 'United States', 1.0),
                    ('San José', 'San José', 'Argentina', 1.0),
                    ('San José', 'San José', 'Costa Rica', 1.0),
                    ('San José', 'San José', 'Philippines', 1.0),
                    ('San José', 'San José', 'Spain', 1.0),
                    ('San José', 'San José', 'United States', 1.0)]
            ),
        ]

        for original, expected in test_cities:
            country_set = {country for _, _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                self.assertListEqual(
                    normalize_city(original, country_set),
                    [Location(canonical_name, matched_name, country, score)
                     for canonical_name, matched_name, country, score in expected]
                )

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_city("plznoname", {"Netherlands", "CN"}), [])
        self.assertEqual(normalize_city("sophisticated name", {"Netherlands", "CN"}), [])

    def test_close_match(self):
        """
        Close matches to the cities map should yield the correct city
        """
        test_cities = [
            ("Toranto", [("Toronto", "Canada", 0.857)]),
            ("Napholi", [("Napoli", "Italy", 0.923)]),
            ("Dallaas", [("Dallas", "United States", 0.923)]),
        ]
        for original, expected_cities in test_cities:
            country_set = {country for _, country, _ in expected_cities}
            with self.subTest(original=original, expected_cities=expected_cities):
                for match, (expected_canonical_name, expected_country, expected_score) in zip(
                        normalize_city(original, country_set), expected_cities
                ):
                    self.assertEqual(match.canonical_name, expected_canonical_name)
                    self.assertEqual(match.matched_name, expected_canonical_name)
                    self.assertEqual(match.country, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_not_close_enough_match(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_cities = ["Teksaas", "Kiyootoo", "Napoulilyla", "Leieieerr"]
        test_country = {"us", "japan", "IT", "GERmany"}
        for original in test_cities:
            with self.subTest(original=original):
                self.assertEqual(normalize_city(original, test_country), [])
                self.assertEqual(normalize_city(original, test_country), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the cities map should yield all correct cities
        """
        test_cities = [
            (
                "Vancoover",
                [
                    ("Vancouver", "Vancouver", "Canada", 0.889),
                    ("Vancouver", "Vancouver", "United States", 0.889)
                ]
            ),
            (
                "Sioul",
                [
                    ('Seoul', 'Sŏul', 'South Korea', 0.889),
                    ('Ingalls', "Soule", 'United States', 0.8),
                    ('Sibul', "Sibul", 'Philippines', 0.8),
                    ('Siolo', "Siolo", 'Italy', 0.8),
                    ('Sitou', "Sitou", 'China', 0.8),
                    ('Soual', "Soual", 'France', 0.8),
                    ('Souel', "Souel", 'France', 0.8),
                    ('Soula', "Soula", 'France', 0.8)
                ]
            ),
            (
                "Canada",
                [
                    ('Canadian', "Canadian", 'United States', 0.857),
                    ('Chandada', "Chandada", 'Australia', 0.857),
                    ('Chantada', "Chantada", 'Spain', 0.857),
                    ('Laguna Seca', "Canadita *", 'United States', 0.857)
                ]
            ),
        ]
        for original, expected in test_cities:
            country_set = {country for _, _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                for match, (expected_canonical_name, expected_matched_name, expected_country, expected_score) in zip(
                        normalize_city(original, restrict_countries=country_set), expected
                ):
                    self.assertEqual(match.canonical_name, expected_canonical_name)
                    self.assertEqual(match.matched_name, expected_matched_name)
                    self.assertEqual(match.country, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_cities_with_multiple_names(self):
        """
        Searching for a city with multiple valid names should yield the correct name
        """
        test_cities = [
            ("Kiev", [("Kyiv", "Kiev", "Ukraine", 1)]),
            ("Makkah", [("Mecca", "Makkah", "Saudi Arabia", 1)]),
            ("Cologne", [("Köln", "Cologne", "Germany", 1)]),
            ("Gothenburg", [("Göteborg", "Gothenburg", "Sweden", 1)]),
        ]
        for original, expected in test_cities:
            country_set = {country for _, _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original, country_set),
                                 [Location(canonical_name, matched_name, country, score)
                                  for canonical_name, matched_name, country, score in expected])

    def test_cities_with_restrict_country(self):
        """
        Searching for a city in one or few specific countries to limit the search space
        """
        test_cities = [
            ("Heidelberg", {"DE"}, [('Heidelberg', 'Germany', 1.0)]),
            ("Heidelberg", {"DE", "South Africa"}, [('Heidelberg', 'Germany', 1.0),
                                                    ('Heidelberg', 'South Africa', 1.0)]),
            ("Heidelberg", {"FR"}, []),
            ("Toronto", {"United States", "GB"}, [('Toronto', 'United States', 1.0)]),
        ]
        for original, country_set, expected in test_cities:
            with self.subTest(original=original, country_set=country_set, expected=expected):
                for match, (expected_canonical_name, expected_country, expected_score) in zip(
                        normalize_city(original, restrict_countries=country_set), expected
                ):
                    self.assertEqual(match.canonical_name, expected_canonical_name)
                    self.assertEqual(match.matched_name, expected_canonical_name)
                    self.assertEqual(match.country, expected_country)
                    self.assertAlmostEqual(match.score, expected_score, places=3)

    def test_thresholds_are_passed(self):
        """
        Test if the thresholds are correctly passed on to the find_closest_string function
        """
        for min_score_levenshtein, min_score_trigram in [(0.8, 0.5), (0.5, 0.8), (0.1, 0.1)]:
            with self.subTest(min_score_levenshtein=min_score_levenshtein, min_score_trigram=min_score_trigram), \
                    patch('text_scrubber.geo.normalize.find_closest_string', side_effect=find_closest_string) as p:
                normalize_city('a city name', {'NL'}, min_score_levenshtein, min_score_trigram)
                self.assertEqual(p.call_args[0][-2:], (min_score_levenshtein, min_score_trigram))


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
