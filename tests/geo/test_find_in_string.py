import unittest

from text_scrubber.geo.find_in_string import (find_city_in_string, find_country_in_string, find_region_in_string,
                                              CountryMatch, LocationMatch)


class FindCountryInStringTest(unittest.TestCase):
    def test_find_single_country_in_string(self):
        """
        examine find_country_in_string where we expect only a single match
        """
        test_samples = [
            (
                "Fur Museum, 7884 Fur, Denmark.",
                [
                    CountryMatch(
                        substring_range=(22, 29),
                        substring="Denmark",
                        canonical_name="Denmark",
                        matched_name="Denmark",
                        score=1.0,
                    )
                ],
            ),
            (
                "The University of Queensland Diamantina Institute, The University of Queensland, Translational "
                "Research Institute, Woolloongabba, Queensland, Australia",
                [
                    CountryMatch(
                        substring_range=(142, 151),
                        substring="Australia",
                        canonical_name="Australia",
                        matched_name="Australia",
                        score=1.0,
                    )
                ],
            ),
            (
                "Institute of Plant Sciences, University of Bern, Bern 3005, Switzerl.",
                [
                    CountryMatch(
                        substring_range=(60, 68),
                        substring="Switzerl",
                        canonical_name="Switzerland",
                        matched_name="Switzerland",
                        score=0.842,
                    )
                ],
            ),
            (
                "0000 0004 0581 2008, grid. 451052. 7, Essex Partnership University NHS Foundation Trust, Essex SS11 "
                "7XX UK",
                [
                    CountryMatch(
                        substring_range=(104, 106),
                        substring="UK",
                        canonical_name="United Kingdom",
                        matched_name="Uk",
                        score=1.0,
                    )
                ],
            ),
            # special case of blacklist/whitelist
            (
                "University of Bern Hochschulstrasse 4 3012CH Bern Switzerland.",
                [
                    CountryMatch(
                        substring_range=(50, 61),
                        substring="Switzerland",
                        canonical_name="Switzerland",
                        matched_name="Switzerland",
                        score=1.0,
                    )
                ],
            ),
            (
                "Peking University, 5 Yiheyuan Rd, Haidian District, Beijing, CH, 100871",
                [
                    CountryMatch(
                        substring_range=(61, 63),
                        substring="CH",
                        canonical_name="China",
                        matched_name="Ch",
                        score=1.0,
                    )
                ]
            ),
            # special case of "Papua New Guinea"
            (
                "Divine Word University, Konedobu, NCD 131, Madang, Papua New Guinea.",
                [
                    CountryMatch(
                        substring_range=(51, 67),
                        substring="Papua New Guinea",
                        canonical_name="Papua New Guinea",
                        matched_name="Papua New Guinea",
                        score=1.0,
                    )
                ],
            ),
        ]
        for original, expected_matches in test_samples:
            with self.subTest(original=original, expected_matches=expected_matches):
                extracted_countries = find_country_in_string(original)
                for expected_match, extracted_country in zip(expected_matches, extracted_countries):
                    self.assertEqual(
                        extracted_country.canonical_name, expected_match.canonical_name
                    )
                    self.assertEqual(
                        extracted_country.matched_name, expected_match.matched_name
                    )
                    self.assertAlmostEqual(
                        extracted_country.score, expected_match.score, places=3
                    )
                    self.assertEqual(
                        extracted_country.substring_range,
                        expected_match.substring_range,
                    )

    def test_find_multiple_matches_country_name_in_string(self):
        """
        examine find_country_in_string where we expect multiple matches
        """
        test_samples = [
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), Texel, The"
                " Netherlands",
                [
                    CountryMatch(
                        substring_range=(45, 56),
                        substring="Netherlands",
                        canonical_name="Netherlands",
                        matched_name="Netherlands",
                        score=1.0,
                    ),
                    CountryMatch(
                        substring_range=(103, 114),
                        substring="Netherlands",
                        canonical_name="Netherlands",
                        matched_name="Netherlands",
                        score=1.0,
                    ),
                ],
            ),
            (
                "International Centre for Radio Astronomy Research (ICRAR), M468, University of Western Australia, "
                "Crawley, WA 6009, Australia",
                [
                    CountryMatch(
                        substring_range=(87, 96),
                        substring="Australia",
                        canonical_name="Australia",
                        matched_name="Australia",
                        score=1.0,
                    ),
                    CountryMatch(
                        substring_range=(116, 125),
                        substring="Australia",
                        canonical_name="Australia",
                        matched_name="Australia",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Institute of Biochemistry and Genetics, Ufa Science Center, Russian Academy of Sciences, Ufa, Russian"
                " Federation.",
                [
                    CountryMatch(
                        substring_range=(94, 112),
                        substring="Russian Federation",
                        canonical_name="Russia",
                        matched_name="Russian Federation",
                        score=1.0,
                    ),
                    CountryMatch(
                        substring_range=(60, 67),
                        substring="Russian",
                        canonical_name="Russia",
                        matched_name="Russia",
                        score=0.923,
                    ),
                ],
            ),
            # case with multiple distinguished country names
            (
                "Institute of German study, Accra, Ghana",
                [
                    CountryMatch(
                        substring_range=(34, 39),
                        substring='Ghana',
                        canonical_name='Ghana',
                        matched_name='Ghana',
                        score=1.0
                    ),
                    CountryMatch(
                        substring_range=(13, 19),
                        substring='German',
                        canonical_name='Germany',
                        matched_name='Germany',
                        score=0.923
                    )
                ]
            ),
        ]
        for original, expected_matches in test_samples:
            with self.subTest(original=original, expected_matches=expected_matches):
                extracted_countries = find_country_in_string(original)
                for expected_match, extracted_country in zip(expected_matches, extracted_countries):
                    self.assertEqual(
                        extracted_country.canonical_name, expected_match.canonical_name
                    )
                    self.assertEqual(
                        extracted_country.matched_name, expected_match.matched_name
                    )
                    self.assertAlmostEqual(
                        extracted_country.score, expected_match.score, places=3
                    )
                    self.assertEqual(
                        extracted_country.substring_range,
                        expected_match.substring_range,
                    )

    def test_find_no_matches_country_name_in_string(self):
        """
        When the input string doesn't contain the name of a country it should return an empty list
        """
        test_samples = [
            (
                "Department of Biological Oceanography, Royal Institute for Sea Research (NIOZ), Texel",
                [],
            ),
            (
                "International Centre for Radio Astronomy Research (ICRAR), M468, University of West Crawley, WA 6009",
                [],
            ),
            (
                "Institute of Biochemistry and Genetics, Ufa Science Center, Academy of Sciences, Ufa",
                [],
            ),
        ]
        for original, expected_match in test_samples:
            with self.subTest(original=original, expected_match=expected_match):
                extracted_country = find_country_in_string(original)
                self.assertEqual(extracted_country, expected_match)


class FindCityInStringTest(unittest.TestCase):
    def test_find_multiple_cities_in_string(self):
        """
        examine find_city_in_string where we expect multiple matches
        """
        test_samples = [
            (
                "Météorage Pau France",
                {"France"},
                [
                    LocationMatch(
                        substring_range=(10, 13),
                        substring="Pau",
                        canonical_name="Pau",
                        matched_name="Pau",
                        country="France",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(14, 20),
                        substring="France",
                        canonical_name="La Frasnée",
                        matched_name="La Frasnée",
                        country="France",
                        score=0.909,
                    )
                ],
            ),
            (
                "Bavarian Environment Agency, Hans Högn Straße 12, 95030 Hof Saale, Bavaria, Germany",
                {"Germany"},
                [
                    LocationMatch(
                        substring_range=(56, 59),
                        substring="Hof",
                        canonical_name="Hof",
                        matched_name="Hof",
                        country="Germany",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(60, 65),
                        substring="Saale",
                        canonical_name="Saal",
                        matched_name="Saal",
                        country="Germany",
                        score=0.889,
                    ),
                    LocationMatch(
                        substring_range=(39, 45),
                        substring="Straße",
                        canonical_name="Trassem",
                        matched_name="Trassem",
                        country="Germany",
                        score=0.857,
                    )
                ],
            ),
            (
                "Institute of Molecular Medicine and Max Planck Research Department of Stem Cell Aging, University of "
                "Ulm, Ulm, Germany",
                {"Germany"},
                [
                    LocationMatch(
                        substring_range=(101, 104),
                        substring='Ulm',
                        canonical_name='Ulm',
                        matched_name='Ulm',
                        country="Germany",
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(106, 109),
                        substring='Ulm',
                        canonical_name='Ulm',
                        matched_name='Ulm',
                        country="Germany",
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(40, 46),
                        substring='Planck',
                        canonical_name='Planegg',
                        matched_name='Planegg',
                        country="Germany",
                        score=0.923
                    ),
                    LocationMatch(
                        substring_range=(80, 85),
                        substring='Aging',
                        canonical_name='Waging am See',
                        matched_name='Waging am See',
                        country="Germany",
                        score=0.909
                    )
                ]
            ),
            (
                "University of Bern Hochschulstrasse 4 3012CH Bern Switzerland.",
                {"Switzerland"},
                [
                    LocationMatch(
                        substring_range=(14, 18),
                        substring="Bern",
                        canonical_name="Bern",
                        matched_name="Bern",
                        country="Switzerland",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(45, 49),
                        substring="Bern",
                        canonical_name="Bern",
                        matched_name="Bern",
                        country="Switzerland",
                        score=1.0,
                    ),
                ],
            ),
            # special case of "new york city"
            (
                "Department of Economics, School of Humanities and Social Sciences, Rensselaer Polytechnic Institute "
                "(RPI), Sage Laboratories Room 3407, Troy, New York 12180, United States",
                {"United States"},
                [
                    LocationMatch(
                        substring_range=(67, 77),
                        substring="Rensselaer",
                        canonical_name="Rensselaer",
                        matched_name="Rensselaer",
                        country="United States",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(136, 140),
                        substring="Troy",
                        canonical_name="Troy",
                        matched_name="Troy",
                        country="United States",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(142, 150),
                        substring="New York",
                        canonical_name="New York City",
                        matched_name="New York City",
                        country="United States",
                        score=1.0,
                    ),
                ],
            ),
        ]
        for original, country, expected_matches in test_samples:
            with self.subTest(
                original=original, country=country, expected_matches=expected_matches
            ):
                extracted_cities = find_city_in_string(original, country)
                for expected_match, extracted_city in zip(
                    expected_matches, extracted_cities
                ):
                    self.assertEqual(
                        extracted_city.canonical_name, expected_match.canonical_name
                    )
                    self.assertAlmostEqual(
                        extracted_city.score, expected_match.score, places=3
                    )
                    self.assertEqual(
                        extracted_city.substring_range, expected_match.substring_range
                    )

    def test_find_no_matches_in_string(self):
        """
        When the input string doesn't contains a city name but maybe a region name it should return an empty list
        """
        test_samples = [
            (
                "Fur Museum, 7884 Fur, Denmark.",
                {"Denmark"},
                []
            ),
            (
                "Centre of Excellence for Omics Driven Computational Biodiscovery, AIMST University, Kedah, Malaysia.",
                {"Malaysia"},
                [],
            ),
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), The"
                " Netherlands",
                {"Netherlands"},
                [],
            ),
        ]
        for original, country, expected_match in test_samples:
            with self.subTest(
                original=original, country=country, expected_match=expected_match
            ):
                extracted_city = find_city_in_string(original, country)
                self.assertEqual(extracted_city, expected_match)


class FindRegionInStringTest(unittest.TestCase):
    def test_find_multiple_regions_in_string(self):
        """
        examine find_region_in_string where we expect multiple matches
        """
        test_samples = [
            (
                "Fur Museum, 7884 Fur, Denmark.",
                {"Denmark"},
                [
                    LocationMatch(
                        substring_range=(0, 3),
                        substring="Fur",
                        canonical_name="Fur",
                        matched_name="Fur",
                        country="Denmark",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(17, 20),
                        substring="Fur",
                        canonical_name="Fur",
                        matched_name="Fur",
                        country="Denmark",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(22, 29),
                        substring="Denmark",
                        canonical_name="Kingdom of Denmark",
                        matched_name="Denmark",
                        country="Denmark",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Centre of Excellence for Omics Driven Computational Biodiscovery, AIMST University, Kedah, Malaysia.",
                {"Malaysia"},
                [
                    LocationMatch(
                        substring_range=(84, 89),
                        substring="Kedah",
                        canonical_name="Kedah",
                        matched_name="Kedah",
                        country="Malaysia",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(91, 99),
                        substring="Malaysia",
                        canonical_name="Malaysia",
                        matched_name="Malaysia",
                        country="Malaysia",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), Texel, The"
                " Netherlands",
                {"Netherlands"},
                [
                    LocationMatch(
                        substring_range=(45, 56),
                        substring="Netherlands",
                        canonical_name="Kingdom of the Netherlands",
                        matched_name="Netherlands",
                        country="Netherlands",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(92, 97),
                        substring="Texel",
                        canonical_name="Texel",
                        matched_name="Texel",
                        country="Netherlands",
                        score=1.0,
                    ),
                    LocationMatch(
                        substring_range=(103, 114),
                        substring="Netherlands",
                        canonical_name="Kingdom of the Netherlands",
                        matched_name="Netherlands",
                        country="Netherlands",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Institute of General Physiology, University of Ulm, Albert Einstein Allee 11, 89081 Ulm, Germany.",
                {"Germany"},
                [
                    LocationMatch(
                        substring_range=(47, 50),
                        substring='Ulm',
                        canonical_name='Ulm',
                        matched_name='Ulm',
                        country='Germany',
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(52, 58),
                        substring='Albert',
                        canonical_name='Albert',
                        matched_name='Albert',
                        country='Germany',
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(68, 73),
                        substring='Allee',
                        canonical_name='Allee',
                        matched_name='Allee',
                        country='Germany',
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(84, 87),
                        substring='Ulm',
                        canonical_name='Ulm',
                        matched_name='Ulm',
                        country='Germany',
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(89, 96),
                        substring='Germany',
                        canonical_name='Federal Republic of Germany',
                        matched_name='Germany',
                        country='Germany',
                        score=1.0
                    ),
                    LocationMatch(
                        substring_range=(59, 67),
                        substring='Einstein',
                        canonical_name='Beinstein',
                        matched_name='Beinstein',
                        country='Germany',
                        score=0.9411764705882353
                    )
                ],
            ),
        ]
        for original, country, expected_matches in test_samples:
            with self.subTest(
                original=original, country=country, expected_matches=expected_matches
            ):
                extracted_regions = find_region_in_string(original, country)
                for expected_match, extracted_region in zip(
                    expected_matches, extracted_regions
                ):
                    self.assertEqual(
                        extracted_region.canonical_name, expected_match.canonical_name
                    )
                    self.assertAlmostEqual(
                        extracted_region.score, expected_match.score, places=3
                    )
                    self.assertEqual(
                        extracted_region.substring_range, expected_match.substring_range
                    )
