import unittest

from text_scrubber.geo.find_in_string import (ExtractedLocation, find_city_in_string, find_country_in_string,
                                              find_region_in_string, Range)
from text_scrubber.geo.normalize import Location


class FindCountryInStringTest(unittest.TestCase):
    def test_find_single_country_in_string(self):
        """
        examine find_country_in_string where we expect only a single match
        """
        test_samples = [
            (
                "Fur Museum, 7884 Fur, Denmark.",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Denmark",
                                          matched_name="Denmark",
                                          country=None,
                                          score=1.0),
                        substring="Denmark",
                        substring_range=Range(22, 29)
                    )
                ],
            ),
            (
                "The University of Queensland Diamantina Institute, The University of Queensland, Translational "
                "Research Institute, Woolloongabba, Queensland, Australia",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Australia",
                                          matched_name="Australia",
                                          country=None,
                                          score=1.0),
                        substring="Australia",
                        substring_range=Range(142, 151)
                    )
                ],
            ),
            (
                "Institute of Plant Sciences, University of Bern, Bern 3005, Switzerl.",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Switzerland",
                                          matched_name="Switzerland",
                                          country=None,
                                          score=0.842),
                        substring="Switzerl",
                        substring_range=Range(60, 68)
                    )
                ],
            ),
            (
                "0000 0004 0581 2008, grid. 451052. 7, Essex Partnership University NHS Foundation Trust, Essex SS11 "
                "7XX UK",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="United Kingdom",
                                          matched_name="UK",
                                          country=None,
                                          score=1.0),
                        substring="UK",
                        substring_range=Range(104, 106)
                    )
                ],
            ),
            # special case of blacklist/whitelist
            (
                "University of Bern Hochschulstrasse 4 3012CH Bern Switzerland.",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Switzerland",
                                          matched_name="Switzerland",
                                          country=None,
                                          score=1.0),
                        substring="Switzerland",
                        substring_range=Range(50, 61)
                    )
                ],
            ),
            (
                "Peking University, 5 Yiheyuan Rd, Haidian District, Beijing, CH, 100871",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Switzerland",
                                          matched_name="CH",
                                          country=None,
                                          score=1.0),
                        substring="CH",
                        substring_range=Range(61, 63)
                    )
                ]
            ),
            # special case of "Papua New Guinea"
            (
                "Divine Word University, Konedobu, NCD 131, Madang, Papua New Guinea.",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Papua New Guinea",
                                          matched_name="Papua New Guinea",
                                          country=None,
                                          score=1.0),
                        substring="Papua New Guinea",
                        substring_range=Range(51, 67)
                    )
                ],
            ),
        ]
        for original, expected_matches in test_samples:
            with self.subTest(original=original, expected_matches=expected_matches):
                extracted_countries = find_country_in_string(original)
                for expected_match, extracted_country in zip(expected_matches, extracted_countries):
                    self.assertEqual(
                        extracted_country.location.canonical_name, expected_match.location.canonical_name
                    )
                    self.assertEqual(
                        extracted_country.location.matched_name, expected_match.location.matched_name
                    )
                    self.assertAlmostEqual(
                        extracted_country.location.score, expected_match.location.score, places=3
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
                    ExtractedLocation(
                        location=Location(canonical_name="Netherlands",
                                          matched_name="Netherlands",
                                          country=None,
                                          score=1.0),
                        substring="Netherlands",
                        substring_range=Range(45, 56)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Netherlands",
                                          matched_name="Netherlands",
                                          country=None,
                                          score=1.0),
                        substring="Netherlands",
                        substring_range=Range(103, 114)
                    ),
                ],
            ),
            (
                "International Centre for Radio Astronomy Research (ICRAR), M468, University of Western Australia, "
                "Crawley, WA 6009, Australia",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Australia",
                                          matched_name="Australia",
                                          country=None,
                                          score=1.0),
                        substring="Australia",
                        substring_range=Range(87, 96)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Australia",
                                          matched_name="Australia",
                                          country=None,
                                          score=1.0),
                        substring="Australia",
                        substring_range=Range(116, 125)
                    ),
                ],
            ),
            (
                "Institute of Biochemistry and Genetics, Ufa Science Center, Russian Academy of Sciences, Ufa, Russian"
                " Federation.",
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Russia",
                                          matched_name="Russian Federation",
                                          country=None,
                                          score=1.0),
                        substring="Russian Federation",
                        substring_range=Range(94, 112)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Russia",
                                          matched_name="Russia",
                                          country=None,
                                          score=0.923),
                        substring="Russian",
                        substring_range=Range(60, 67)
                    ),
                ],
            ),
            # case with multiple distinguished country names
            (
                "Institute of German study, Accra, Ghana",
                [
                    ExtractedLocation(
                        location=Location(canonical_name='Ghana',
                                          matched_name='Ghana',
                                          country=None,
                                          score=1.0),
                        substring='Ghana',
                        substring_range=Range(34, 39)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Germany',
                                          matched_name='Germany',
                                          country=None,
                                          score=0.923),
                        substring='German',
                        substring_range=Range(13, 19)
                    )
                ]
            ),
        ]
        for original, expected_matches in test_samples:
            with self.subTest(original=original, expected_matches=expected_matches):
                extracted_countries = find_country_in_string(original)
                for expected_match, extracted_country in zip(expected_matches, extracted_countries):
                    self.assertEqual(
                        extracted_country.location.canonical_name, expected_match.location.canonical_name
                    )
                    self.assertEqual(
                        extracted_country.location.matched_name, expected_match.location.matched_name
                    )
                    self.assertAlmostEqual(
                        extracted_country.location.score, expected_match.location.score, places=3
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
                    ExtractedLocation(
                        location=Location(canonical_name="Pau",
                                          matched_name="Pau",
                                          country="France",
                                          score=1.0),
                        substring="Pau",
                        substring_range=Range(10, 13)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="La Frasnée",
                                          matched_name="La Frasnée",
                                          country="France",
                                          score=0.909),
                        substring="France",
                        substring_range=Range(14, 20)
                    )
                ],
            ),
            (
                "Bavarian Environment Agency, Hans Högn Straße 12, 95030 Hof Saale, Bavaria, Germany",
                {"Germany"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Hof",
                                          matched_name="Hof",
                                          country="Germany",
                                          score=1.0),
                        substring="Hof",
                        substring_range=Range(56, 59)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Saal",
                                          matched_name="Saal",
                                          country="Germany",
                                          score=0.889),
                        substring="Saale",
                        substring_range=Range(60, 65)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Trassem",
                                          matched_name="Trassem",
                                          country="Germany",
                                          score=0.857),
                        substring="Straße",
                        substring_range=Range(39, 45)
                    )
                ],
            ),
            (
                "Institute of Molecular Medicine and Max Planck Research Department of Stem Cell Aging, University of "
                "Ulm, Ulm, Germany",
                {"Germany"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name='Ulm',
                                          matched_name='Ulm',
                                          country="Germany",
                                          score=1.0),
                        substring='Ulm',
                        substring_range=Range(101, 104)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Ulm',
                                          matched_name='Ulm',
                                          country="Germany",
                                          score=1.0),
                        substring='Ulm',
                        substring_range=Range(106, 109)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Planegg',
                                          matched_name='Planegg',
                                          country="Germany",
                                          score=0.923),
                        substring='Planck',
                        substring_range=Range(40, 46)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Waging am See',
                                          matched_name='Waging am See',
                                          country="Germany",
                                          score=0.909),
                        substring='Aging',
                        substring_range=Range(80, 85)
                    )
                ]
            ),
            (
                "University of Bern Hochschulstrasse 4 3012CH Bern Switzerland.",
                {"Switzerland"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Bern",
                                          matched_name="Bern",
                                          country="Switzerland",
                                          score=1.0),
                        substring="Bern",
                        substring_range=Range(14, 18)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Bern",
                                          matched_name="Bern",
                                          country="Switzerland",
                                          score=1.0),
                        substring="Bern",
                        substring_range=Range(45, 49)
                    ),
                ],
            ),
            # special case of "new york city"
            (
                "Department of Economics, School of Humanities and Social Sciences, Rensselaer Polytechnic Institute "
                "(RPI), Sage Laboratories Room 3407, Troy, New York 12180, United States",
                {"United States"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Rensselaer",
                                          matched_name="Rensselaer",
                                          country="United States",
                                          score=1.0),
                        substring="Rensselaer",
                        substring_range=Range(67, 77)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Troy",
                                          matched_name="Troy",
                                          country="United States",
                                          score=1.0),
                        substring="Troy",
                        substring_range=Range(136, 140)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="New York City",
                                          matched_name="New York City",
                                          country="United States",
                                          score=1.0),
                        substring="New York",
                        substring_range=Range(142, 150)
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
                        extracted_city.location.canonical_name, expected_match.location.canonical_name
                    )
                    self.assertAlmostEqual(
                        extracted_city.location.score, expected_match.location.score, places=3
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
                    ExtractedLocation(
                        location=Location(canonical_name="Fur",
                                          matched_name="Fur",
                                          country="Denmark",
                                          score=1.0),
                        substring="Fur",
                        substring_range=Range(0, 3)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Fur",
                                          matched_name="Fur",
                                          country="Denmark",
                                          score=1.0),
                        substring="Fur",
                        substring_range=Range(17, 20)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Kingdom of Denmark",
                                          matched_name="Denmark",
                                          country="Denmark",
                                          score=1.0),
                        substring="Denmark",
                        substring_range=Range(22, 29)
                    ),
                ],
            ),
            (
                "Centre of Excellence for Omics Driven Computational Biodiscovery, AIMST University, Kedah, Malaysia.",
                {"Malaysia"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Kedah",
                                          matched_name="Kedah",
                                          country="Malaysia",
                                          score=1.0),
                        substring="Kedah",
                        substring_range=Range(84, 89)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Malaysia",
                                          matched_name="Malaysia",
                                          country="Malaysia",
                                          score=1.0),
                        substring="Malaysia",
                        substring_range=Range(91, 99)
                    ),
                ],
            ),
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), Texel, The"
                " Netherlands",
                {"Netherlands"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name="Kingdom of the Netherlands",
                                          matched_name="Netherlands",
                                          country="Netherlands",
                                          score=1.0),
                        substring="Netherlands",
                        substring_range=Range(45, 56)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Texel",
                                          matched_name="Texel",
                                          country="Netherlands",
                                          score=1.0),
                        substring="Texel",
                        substring_range=Range(92, 97)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name="Kingdom of the Netherlands",
                                          matched_name="Netherlands",
                                          country="Netherlands",
                                          score=1.0),
                        substring="Netherlands",
                        substring_range=Range(103, 114)
                    ),
                ],
            ),
            (
                "Institute of General Physiology, University of Ulm, Albert Einstein Allee 11, 89081 Ulm, Germany.",
                {"Germany"},
                [
                    ExtractedLocation(
                        location=Location(canonical_name='Ulm',
                                          matched_name='Ulm',
                                          country='Germany',
                                          score=1.0),
                        substring='Ulm',
                        substring_range=Range(47, 50)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Albert',
                                          matched_name='Albert',
                                          country='Germany',
                                          score=1.0),
                        substring='Albert',
                        substring_range=Range(52, 58)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Allee',
                                          matched_name='Allee',
                                          country='Germany',
                                          score=1.0),
                        substring='Allee',
                        substring_range=Range(68, 73)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Ulm',
                                          matched_name='Ulm',
                                          country='Germany',
                                          score=1.0),
                        substring='Ulm',
                        substring_range=Range(84, 87)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Federal Republic of Germany',
                                          matched_name='Germany',
                                          country='Germany',
                                          score=1.0),
                        substring='Germany',
                        substring_range=Range(89, 96)
                    ),
                    ExtractedLocation(
                        location=Location(canonical_name='Beinstein',
                                          matched_name='Beinstein',
                                          country='Germany',
                                          score=0.9411764705882353),
                        substring='Einstein',
                        substring_range=Range(59, 67)
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
                        extracted_region.location.canonical_name, expected_match.location.canonical_name
                    )
                    self.assertAlmostEqual(
                        extracted_region.location.score, expected_match.location.score, places=3
                    )
                    self.assertEqual(
                        extracted_region.substring_range, expected_match.substring_range
                    )
