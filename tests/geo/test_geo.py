import unittest

from numpy import testing

from text_scrubber.geo.geo import (_clean_geo_string, capitalize_geo_string, normalize_country, normalize_region,
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
                self.assertEqual(normalize_country(original), [(c, 1.0) for c in expected])

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
                self.assertEqual(normalize_country(original), [(c, 1.0) for c in expected])

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
                for (country, score), expected_country, expected_score in zip(
                        normalize_country(original), expected_countries, expected_scores
                ):
                    self.assertEqual(country, expected_country)
                    self.assertAlmostEqual(score, expected_score, places=3)

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
                for (country, score), expected_country, expected_score in zip(
                        normalize_country(original), expected_countries, expected_scores
                ):
                    self.assertEqual(country, expected_country)
                    self.assertAlmostEqual(score, expected_score, places=3)

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
                for (country, score), expected_country, expected_score in zip(
                        normalize_country(original), expected_countries, expected_scores
                ):
                    self.assertEqual(country, expected_country)
                    self.assertAlmostEqual(score, expected_score, places=3)


class NormalizeRegionsTest(unittest.TestCase):

    def test_part_of_known_regions(self):
        """
        Test input that is part of the regions map
        """
        test_regions = [
            ('Queensland', [('State of Queensland', 'Australia')]),
            ('QLd', [('State of Queensland', 'Australia')]),
            ('Rio de Janeiro', [('Rio de Janeiro', 'Brazil')]),
            ('ON', [('Ontario', 'Canada')]),
            ('okinaWA', [('Okinawa', 'Japan')]),
            ('Georgia', [('Georgia', 'United States')]),
            ('NY', [('New York', 'United States')]),
        ]
        for original, expected in test_regions:
            country_set = {country for _, country in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_region(original, restrict_countries=country_set),
                                 [(s, c, 1.0) for s, c in expected])

    def test_multiple_matches(self):
        """
        Test input that is part of the regions map that return multiple matches
        """
        test_regions = [
            ('WA', [('State of Western Australia', 'Australia'), ('Washington', 'United States')]),
            ('AR', [('Arkansas', 'United States'), ('State of Arunāchal Pradesh', 'India')]),
            ('nl', [('Newfoundland and Labrador', 'Canada'), ('State of Nāgāland', 'India')])
        ]
        for original, expected in test_regions:
            country_set = {country for _, country in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_region(original, restrict_countries=country_set),
                                 [(s, c, 1.0) for s, c in expected])

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
            ('Ilinios', [('Illinois', 'United States')], [0.8]),
            ('Saytama-Ken', [('Saitama-ken', 'Japan')], [0.909]),
            ('kashmir and jannu', [('State of Jammu and Kashmīr', 'India')], [0.6]),
            ('King Kong', [('Kalingkong', 'China')], [0.842])
        ]
        for original, expected_regions, expected_scores in test_regions:
            country_set = {country for _, country in expected_regions}
            with self.subTest(original=original, expected_regions=expected_regions, expected_scores=expected_scores):
                for (region, country, score), expected_region, expected_score in zip(
                        normalize_region(original, restrict_countries=country_set), expected_regions, expected_scores
                ):
                    self.assertEqual((region, country), expected_region)
                    self.assertAlmostEqual(score, expected_score, places=3)

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
            ('Jiangs', [('Jiangsu Sheng', 'China'), ('Jiyang Village', 'China')], [0.923, 0.833]),
            ('oka', [('Mōka-machi', 'Japan'), ('Sōka Shi', 'Japan')], [0.857, 0.857]),
            ('VWA', [('State of Western Australia', 'Australia'), ('Virginia', 'United States'),
                     ('Washington', 'United States')], [0.8, 0.8, 0.8])
        ]
        for original, expected_regions, expected_scores in test_regions:
            country_set = {country for _, country in expected_regions}
            with self.subTest(original=original, expected_regions=expected_regions, expected_scores=expected_scores):
                for (region, country, score), expected_region, expected_score in zip(
                        normalize_region(original, restrict_countries=country_set), expected_regions, expected_scores
                ):
                    self.assertEqual((region, country), expected_region)
                    self.assertAlmostEqual(score, expected_score, places=3)


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
                                 [(city, country, score) for city, country, score in expected])

    def test_multiple_matches(self):
        """
        Test input that is part of the cities map that return multiple matches
        """
        test_cities = [
            (
                "woodstock",
                [
                    ("Woodstock", "Australia", 1),
                    ("Woodstock", "Canada", 1),
                    ("Woodstock", "United Kingdom", 1),
                    ("Woodstock", "United States", 1),
                ],
            ),
            (
                "heidelberg",
                [
                    ("Heidelberg", "Germany", 1),
                    ("Heidelberg", "South Africa", 1),
                    ("Heidelberg", "United States", 1)
                ],
            ),
            (
                "San Jose",
                [
                    ('San Jose', 'United States', 1.0),
                    ('San Jose Village', 'United States', 1.0),
                    ('San José', 'Argentina', 1.0),
                    ('San José', 'Costa Rica', 1.0),
                    ('San José', 'Philippines', 1.0),
                    ('San José', 'Spain', 1.0),
                    ('San José', 'United States', 1.0)
                ]
            ),
        ]

        for original, expected in test_cities:
            country_set = {country for _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                self.assertCountEqual(
                    normalize_city(original, country_set),
                    [(city, country, score) for city, country, score in expected]
                )

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_city("plznoname", {"Netherlands", "CN"}), [])
        self.assertEqual(normalize_city("sophisticated name", {"Netherlands", "CN"}), [])

    def test_removal_of_city_suffixes(self):
        """
        Suffixes ' si', ' ri' and ' dong' should be removed before matching
        """
        test_cities = [
            ("wonju si", [("Wŏnju", "South Korea", 1)]),
            ("Zhaoqing dong", [("Zhaoqing", "China", 1)]),
        ]
        for original, expected in test_cities:
            country_set = {country for _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original, country_set),
                                 [(city, country, score) for city, country, score in expected])

    def test_close_match(self):
        """
        Close matches to the cities map should yield the correct city
        """
        test_cities = [
            ("Toranto", [("Toronto", "Canada", 0.857)]),
            ("Napholi", [("Napoli", "Italy", 0.923)]),
            ("Dallaas", [("Dallas", "United States", 0.923)]),
        ]
        for original, expected in test_cities:
            country_set = {country for _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                [(city, country, score)] = normalize_city(original, country_set)
                [(expected_city, expected_country, expected_scores)] = expected
                self.assertEqual((expected_city, expected_country), (city, country))
                self.assertAlmostEqual(score, expected_scores, places=3)

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
        Close matches to the regions map should yield all correct regions
        """
        test_cities = [
            (
                "Vancoover",
                [
                    ("Vancouver", "Canada", 0.889),
                    ("Vancouver", "United States", 0.889)
                ]
            ),
            (
                "Sioul",
                [
                    ('Seoul', 'South Korea', 0.889),
                    ('Ingalls', 'United States', 0.8),
                    ('Sibul', 'Philippines', 0.8),
                    ('Siolo', 'Italy', 0.8),
                    ('Sitou', 'China', 0.8),
                    ('Soual', 'France', 0.8),
                    ('Souel', 'France', 0.8),
                    ('Soula', 'France', 0.8)
                ]
            ),
            (
                "Canada",
                [
                    ('Canadian', 'United States', 0.857),
                    ('Chandada', 'Australia', 0.857),
                    ('Chantada', 'Spain', 0.857),
                    ('Laguna Seca', 'United States', 0.857)
                ]
            ),
        ]
        for original, expected in test_cities:
            country_set = {country for _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                out_list = normalize_city(original, country_set)
                expected_score_list = [score for (_, _, score) in expected]
                expected_city_country_list = [(expected_city, expected_country) for (expected_city, expected_country, _)
                                              in expected]
                score_list = [score for (_, _, score) in out_list]
                city_country_list = [(city, country) for (city, country, _) in out_list]
                self.assertCountEqual(expected_city_country_list, city_country_list)
                testing.assert_almost_equal(expected_score_list, score_list, 3)

    def test_cities_with_multiple_names(self):
        """
        Searching for a city with multiple valid names should yield the correct name
        """
        test_cities = [
            ("Kiev", [("Kyiv", "Ukraine", 1)]),
            ("Makkah", [("Mecca", "Saudi Arabia", 1)]),
            ("Cologne", [("Köln", "Germany", 1)]),
            ("Gothenburg", [("Göteborg", "Sweden", 1)]),
        ]
        for original, expected in test_cities:
            country_set = {country for _, country, _ in expected}
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original, country_set),
                                 [(city, country, score) for city, country, score in expected])

    def test_cities_with_restrict_country(self):
        """
        Searching for a city in one or few specific countries to limit the search space
        """
        test_cities = [
            (["Heidelberg", {"DE"}], [('Heidelberg', 'Germany', 1.0)]),
            (["Heidelberg", {"DE", "South Africa"}],
             [('Heidelberg', 'South Africa', 1.0), ('Heidelberg', 'Germany', 1.0)]),
            (["Heidelberg", {"FR"}], []),
            (["Toronto", {"United States", "GB"}], [('Toronto', 'United States', 1.0)]),
        ]
        for original, expected in test_cities:
            country_set = original[1]
            with self.subTest(original=original, expected=expected):
                out_list = normalize_city(original[0], country_set)
                expected_score_list = sorted([score for (_, _, score) in expected], reverse=True)
                expected_city_country_list = [(expected_city, expected_country) for (expected_city, expected_country, _)
                                              in expected]
                score_list = [score for (_, _, score) in out_list]
                city_country_list = [(city, country) for (city, country, _) in out_list]
                self.assertCountEqual(expected_city_country_list, city_country_list)
                testing.assert_almost_equal(expected_score_list, score_list, 3)


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
            ('北京', 'beijing'),
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
