import unittest

from numpy import testing

from text_scrubber.geo.geo import (_clean_geo_string, capitalize_geo_string, normalize_country, normalize_state,
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
                self.assertEqual(normalize_country(original, return_scores=False), expected)
                self.assertEqual(normalize_country(original, return_scores=True), [(c, 1.0) for c in expected])

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_country('*', return_scores=False), [])
        self.assertEqual(normalize_country('fooBar', return_scores=True), [])
        self.assertEqual(normalize_country('New South Wales', return_scores=False), [])
        self.assertEqual(normalize_country('Paris', return_scores=True), [])

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
                self.assertEqual(normalize_country(original, return_scores=False), expected)
                self.assertEqual(normalize_country(original, return_scores=True), [(c, 1.0) for c in expected])

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
                self.assertEqual(normalize_country(original, return_scores=False), expected_countries)
                for (country, score), expected_country, expected_score in zip(
                        normalize_country(original, return_scores=True), expected_countries, expected_scores
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
                self.assertEqual(normalize_country(original, return_scores=False), [])
                self.assertEqual(normalize_country(original, return_scores=True), [])

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
                self.assertEqual(normalize_country(original, return_scores=False), expected_countries)
                for (country, score), expected_country, expected_score in zip(
                        normalize_country(original, return_scores=True), expected_countries, expected_scores
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
                self.assertEqual(normalize_country(original, return_scores=False), expected_countries)
                for (country, score), expected_country, expected_score in zip(
                        normalize_country(original, return_scores=True), expected_countries, expected_scores
                ):
                    self.assertEqual(country, expected_country)
                    self.assertAlmostEqual(score, expected_score, places=3)


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
                self.assertEqual(normalize_state(original, return_scores=False), expected)
                self.assertEqual(normalize_state(original, return_scores=True), [(s, c, 1.0) for s, c in expected])

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
                self.assertEqual(normalize_state(original, return_scores=False), expected)
                self.assertEqual(normalize_state(original, return_scores=True), [(s, c, 1.0) for s, c in expected])

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_state('*', return_scores=False), [])
        self.assertEqual(normalize_state('fooBar', return_scores=True), [])
        self.assertEqual(normalize_state('Brazil', return_scores=False), [])
        self.assertEqual(normalize_state('Paris', return_scores=True), [])

    def test_close_match(self):
        """
        Close matches to the states map should yield the correct state
        """
        test_states = [
            ('Ilinios', [('Illinois', 'United States')], [0.8]),
            ('Saytama', [('Saitama', 'Japan')], [0.857]),
            ('kashmir and jannu', [('Jammu and Kashmir', 'India')], [0.6]),
            ('King Kong', [('Hong Kong', 'China')], [0.5])
        ]
        for original, expected_states, expected_scores in test_states:
            with self.subTest(original=original, expected_states=expected_states, expected_scores=expected_scores):
                self.assertEqual(normalize_state(original, return_scores=False), expected_states)
                for (state, country, score), expected_state, expected_score in zip(
                        normalize_state(original, return_scores=True), expected_states, expected_scores
                ):
                    self.assertEqual((state, country), expected_state)
                    self.assertAlmostEqual(score, expected_score, places=3)

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
                self.assertEqual(normalize_state(original, return_scores=False), [])
                self.assertEqual(normalize_state(original, return_scores=True), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the states map should yield all correct states
        """
        test_states = [
            ('Jiang', [('Jiangsu', 'China'), ('Jiangxi', 'China')], [0.833, 0.833]),
            ('oshima', [('Hiroshima', 'Japan'), ('Kagoshima', 'Japan'), ('Tokushima', 'Japan')], [0.8, 0.8, 0.8]),
            ('VWA', [('Virginia', 'United States'), ('Washington', 'United States'),
                     ('Western Australia', 'Australia')], [0.8, 0.8, 0.8])
        ]
        for original, expected_states, expected_scores in test_states:
            with self.subTest(original=original, expected_states=expected_states, expected_scores=expected_scores):
                self.assertEqual(normalize_state(original, return_scores=False), expected_states)
                for (state, country, score), expected_state, expected_score in zip(
                        normalize_state(original, return_scores=True), expected_states, expected_scores
                ):
                    self.assertEqual((state, country), expected_state)
                    self.assertAlmostEqual(score, expected_score, places=3)


class NormalizeCityTest(unittest.TestCase):
    def test_part_of_known_cities(self):
        """
        Test input that is part of the cities map
        """
        test_cities = [
            ("Booleroo", [("Booleroo", "Australia")]),
            ("Leibnitz", [("Leibnitz", "Austria")]),
            ("ivry-sur-seine", [("Ivry Sur Seine", "France")]),
            ("Birjand", [("Birjand", "Iran")]),
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original, return_scores=False), expected)
                self.assertEqual(normalize_city(original, return_scores=True), [(city, country, 1.0) for city, country in expected])

    def test_multiple_matches(self):
        """
        Test input that is part of the cities map that return multiple matches
        """
        test_cities = [
            (
                "woodstock",
                [
                    ("Woodstock", "Australia"),
                    ("Woodstock", "Canada"),
                    ("Woodstock", "United Kingdom"),
                    ("Woodstock", "United States"),
                ],
            ),
            (
                "heidelberg",
                [("Heidelberg", "Germany"), ("Heidelberg", "South Africa"), ("Heidelberg", "United States")],
            ),
            (
                "San Jose",
                [
                    ("San Jose", "Argentina"),
                    ("San Jose", "Costa Rica"),
                    ("San Jose", "Philippines"),
                    ("San Jose", "Spain"),
                    ("San Jose", "United States"),
                ],
            ),
        ]
        
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertCountEqual(normalize_city(original, return_scores=False), expected)
                self.assertCountEqual(
                    normalize_city(original, return_scores=True), [(city, country, 1.0) for city, country in expected]
                )

    def test_no_match(self):
        """
        If nothing matches it should return an empty list
        """
        self.assertEqual(normalize_city("plznoname", return_scores=True), [])
        self.assertEqual(normalize_city("sophisticated name", return_scores=False), [])

    def test_removal_of_city_suffixes(self):
        """
        Suffixes ' si', ' ri' and ' dong' should be removed before matching
        """
        test_cities = [
            ("wonju si", [("Wonju", "South Korea")]),
            ("Bucheon-si", [("Bucheon", "South Korea")]),
            ("Zhaoqing dong", [("Zhaoqing", "China")]),
            ("Sillye I Ri", [("Sillye I", "South Korea")]),
        ]
        for original, expected in test_cities:
            with self.subTest(original=original, expected=expected):
                self.assertEqual(normalize_city(original, return_scores=False), expected)
                self.assertEqual(normalize_city(original, return_scores=True), [(city, country, 1.0) for city, country in expected])

    def test_close_match(self):
        """
        Close matches to the cities map should yield the correct city
        """
        test_cities = [
            ("Toranto", (["Toronto"], "Canada"), 0.857),
            ("Napholi", (["Napoli"], "Italy"), 0.923),
            ("San Deego", (["San Diego"], "United States"), 0.889),
        ]
        for original, expected_cities, expected_scores in test_cities:
            with self.subTest(original=original, expected_cities=expected_cities, expected_scores=expected_scores):
                self.assertIn(expected_cities, normalize_city(original, return_scores=False))
                score_list = [score for (city, country, score) in normalize_city(original, return_scores=True)]
                city_country_list = [
                    (city, country) for (city, country, score) in normalize_city(original, return_scores=True)
                ]
                self.assertIn(expected_cities, city_country_list)
                cities_id = city_country_list.index(expected_cities)
                self.assertAlmostEqual(score_list[cities_id], expected_scores, places=3)

    def test_not_close_enough_match(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_cities = ["Teksaas", "Kiyootoo", "Napoulilyla", "Leieieerr"]
        for original in test_cities:
            with self.subTest(original=original):
                self.assertEqual(normalize_city(original, return_scores=False), [])
                self.assertEqual(normalize_city(original, return_scores=True), [])

    def test_multiple_close_matches(self):
        """
        Close matches to the states map should yield all correct states
        """
        test_cities = [
            ("Vancoover", [(["Vancouver"], "Canada"), (["Vancouver"], "United States")], [0.889, 0.889]),
            (
                "Sioul",
                [
                    (["Sibol", "Sibul"], "Philippines"),
                    (["Siolo"], "Italy"),
                    (["Siou"], "China"),
                    (["Sioux"], "United States"),
                    (["Siyoul"], "South Korea"),
                    (["Soul"], "France"),
                    (["Stoul"], "United Kingdom"),
                ],
                [0.8, 0.8, 0.889, 0.8, 0.909, 0.889, 0.8],
            ),
            (
                "KIWI",
                [
                    (["Kaiwei"], "China"),
                    (["Kii"], "United States"),
                    (["Kiwaki", "Koiwai"], "Japan"),
                    (["Kiwit"], "Philippines"),
                    (["Kwi"], "South Korea"),
                ],
                [0.8, 0.857, 0.8, 0.889, 0.857],
            ),
        ]
        for original, expected_cities, expected_scores in test_cities:
            with self.subTest(original=original, expected_cities=expected_cities, expected_scores=expected_scores):
                self.assertEqual(normalize_city(original, return_scores=False), expected_cities)
                score_list = [score for (city, country, score) in normalize_city(original, return_scores=True)]
                city_country_list = [
                    (city, country) for (city, country, score) in normalize_city(original, return_scores=True)
                ]
                self.assertEqual(city_country_list, expected_cities)
                testing.assert_almost_equal(expected_scores, score_list, 3)


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
