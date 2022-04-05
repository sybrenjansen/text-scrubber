from collections import namedtuple
import unittest

from numpy import testing

from text_scrubber.geo.find_in_string import (
    find_city_in_string,
    find_country_in_string,
    find_region_in_string,
)

# Match object. 'substring_range' is a tuple denoting the start and end idx of the substring in the original string.
Match = namedtuple("Match", ["substring_range", "substring", "normalized", "score"])


class FindCountryInStringTest(unittest.TestCase):
    def test_find_single_country_in_string(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_samples = [
            (
                "Fur Museum, 7884 Fur, Denmark.",
                [
                    Match(
                        substring_range=(22, 29),
                        substring="Denmark",
                        normalized="Denmark",
                        score=1.0,
                    )
                ],
            ),
            (
                "The University of Queensland Diamantina Institute, The University of Queensland, Translational Research Institute, Woolloongabba, Queensland, Australia",
                [
                    Match(
                        substring_range=(142, 151),
                        substring="Australia",
                        normalized="Australia",
                        score=1.0,
                    )
                ],
            ),
            (
                "Centre of Excellence for Omics Driven Computational Biodiscovery, AIMST University, Kedah, Malaysia.",
                [
                    Match(
                        substring_range=(91, 99),
                        substring="Malaysia",
                        normalized="Malaysia",
                        score=1.0,
                    )
                ],
            ),
            # check blacklist and whitelist
            (
                "0000 0004 0581 2008, grid. 451052. 7, Essex Partnership University NHS Foundation Trust, Essex SS11 7XX UK",
                [
                    Match(
                        substring_range=(104, 106),
                        substring="UK",
                        normalized="United Kingdom",
                        score=1.0,
                    )
                ],
            ),
            (
                "University of Bern Hochschulstrasse 4 3012CH Bern Switzerland.",
                [
                    Match(
                        substring_range=(50, 61),
                        substring="Switzerland",
                        normalized="Switzerland",
                        score=1.0,
                    )
                ],
            ),
        ]
        for original, expected_match in test_samples:
            with self.subTest(original=original, expected_match=expected_match):
                extracted_country = find_country_in_string(original)
                self.assertEqual(
                    extracted_country[0].normalized, expected_match[0].normalized
                )
                self.assertEqual(extracted_country[0].score, expected_match[0].score)
                self.assertEqual(
                    extracted_country[0].substring_range,
                    expected_match[0].substring_range,
                )

    def test_find_multiple_matches_country_name_in_string(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_samples = [
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), Texel, The Netherlands",
                [
                    Match(
                        substring_range=(45, 56),
                        substring="Netherlands",
                        normalized="Netherlands",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(103, 114),
                        substring="Netherlands",
                        normalized="Netherlands",
                        score=1.0,
                    ),
                ],
            ),
            (
                "International Centre for Radio Astronomy Research (ICRAR), M468, University of Western Australia, Crawley, WA 6009, Australia",
                [
                    Match(
                        substring_range=(87, 96),
                        substring="Australia",
                        normalized="Australia",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(116, 125),
                        substring="Australia",
                        normalized="Australia",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Institute of Biochemistry and Genetics, Ufa Science Center, Russian Academy of Sciences, Ufa, Russian Federation.",
                [
                    Match(
                        substring_range=(94, 112),
                        substring="Russian Federation",
                        normalized="Russia",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(60, 67),
                        substring="Russian",
                        normalized="Russia",
                        score=0.923,
                    ),
                ],
            ),
        ]
        for original, expected_matches in test_samples:
            with self.subTest(original=original, expected_matches=expected_matches):
                extracted_countries = find_country_in_string(original)
                for expected_match, extracted_country in zip(
                    expected_matches, extracted_countries
                ):
                    self.assertEqual(
                        extracted_country.normalized, expected_match.normalized
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
        When the input string is distorted too much it should return an empty list
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
        When the input string is distorted too much it should return an empty list
        """
        test_samples = [
            (
                "0000 0004 1791 9005, grid. 419257. c, Medical Genome Center, National Center for Geriatrics and Gerontology, Obu Japan",
                {"Japan"},
                [
                    Match(
                        substring_range=(109, 112),
                        substring="Obu",
                        normalized="Ōbu",
                        score=1.0,
                    )
                ],
            ),
            (
                "University of Bern Hochschulstrasse 4 3012CH Bern Switzerland.",
                {"Switzerland"},
                [
                    Match(
                        substring_range=(14, 18),
                        substring="Bern",
                        normalized="Bern",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(45, 49),
                        substring="Bern",
                        normalized="Bern",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Department of Economics, School of Humanities and Social Sciences, Rensselaer Polytechnic Institute (RPI), Sage Laboratories Room 3407, Troy, New York 12180, United States",
                {"United States"},
                [
                    Match(
                        substring_range=(67, 77),
                        substring="Rensselaer",
                        normalized="Rensselaer",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(142, 150),
                        substring="New York",
                        normalized="New York City",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(107, 111),
                        substring="Sage",
                        normalized="Osage",
                        score=0.889,
                    ),
                    Match(
                        substring_range=(125, 129),
                        substring="Room",
                        normalized="Croom",
                        score=0.889,
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
                        extracted_city.normalized, expected_match.normalized
                    )
                    self.assertAlmostEqual(
                        extracted_city.score, expected_match.score, places=3
                    )
                    self.assertEqual(
                        extracted_city.substring_range, expected_match.substring_range
                    )

    def test_find_no_matches_in_string(self):
        """
        When the input string is distorted too much it should return an empty list
        """
        test_samples = [
            ("Fur Museum, 7884 Fur, Denmark.", {"Denmark"}, []),
            (
                "Centre of Excellence for Omics Driven Computational Biodiscovery, AIMST University, Kedah, Malaysia.",
                {"Malaysia"},
                [],
            ),
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), Texel, The Netherlands",
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
        When the input string is distorted too much it should return an empty list
        """
        test_samples = [
            (
                "Fur Museum, 7884 Fur, Denmark.",
                {"Denmark"},
                [
                    Match(
                        substring_range=(0, 3),
                        substring="Fur",
                        normalized="Fur",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(17, 20),
                        substring="Fur",
                        normalized="Fur",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(22, 29),
                        substring="Denmark",
                        normalized="Kingdom of Denmark",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Centre of Excellence for Omics Driven Computational Biodiscovery, AIMST University, Kedah, Malaysia.",
                {"Malaysia"},
                [
                    Match(
                        substring_range=(84, 89),
                        substring="Kedah",
                        normalized="Kedah",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(91, 99),
                        substring="Malaysia",
                        normalized="Malaysia",
                        score=1.0,
                    ),
                ],
            ),
            (
                "Department of Biological Oceanography, Royal Netherlands Institute for Sea Research (NIOZ), Texel, The Netherlands",
                {"Netherlands"},
                [
                    Match(
                        substring_range=(45, 56),
                        substring="Netherlands",
                        normalized="Kingdom of the Netherlands",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(92, 97),
                        substring="Texel",
                        normalized="Texel",
                        score=1.0,
                    ),
                    Match(
                        substring_range=(103, 114),
                        substring="Netherlands",
                        normalized="Kingdom of the Netherlands",
                        score=1.0,
                    ),
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
                        extracted_region.normalized, expected_match.normalized
                    )
                    self.assertAlmostEqual(
                        extracted_region.score, expected_match.score, places=3
                    )
                    self.assertEqual(
                        extracted_region.substring_range, expected_match.substring_range
                    )
