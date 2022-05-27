import unittest

from text_scrubber.geo.resources import add_city_resources, add_country_resources, add_region_resources


class AddCountryResourcesTest(unittest.TestCase):

    def test_structure(self):
        """
        We're not testing everything here, just the structure of the dictionary. The other parts are too much work to
        test and are by proxy tested in other tests
        """
        add_country_resources()
        from text_scrubber.geo.resources import _COUNTRY_RESOURCES

        self.assertListEqual(sorted(_COUNTRY_RESOURCES.keys()),
                             ['all_country_codes', 'countries', 'country_to_normalized_country_map',
                              'normalized_country_to_country_codes_map', 'replacement_patterns'])
        self.assertIsInstance(_COUNTRY_RESOURCES['all_country_codes'], set)
        self.assertIsInstance(_COUNTRY_RESOURCES['countries'], dict)
        self.assertIsInstance(_COUNTRY_RESOURCES['country_to_normalized_country_map'], dict)
        self.assertIsInstance(_COUNTRY_RESOURCES['normalized_country_to_country_codes_map'], dict)
        self.assertIsInstance(_COUNTRY_RESOURCES['replacement_patterns'], list)

        self.assertListEqual(sorted(_COUNTRY_RESOURCES['countries'].keys()),
                             ['canonical_names', 'cleaned_location_map', 'levenshtein', 'trigrams'])
        self.assertIsInstance(_COUNTRY_RESOURCES['countries']['levenshtein'], dict)
        self.assertIsInstance(_COUNTRY_RESOURCES['countries']['trigrams'], dict)
        for size_dict in _COUNTRY_RESOURCES['countries']['levenshtein'].values():
            self.assertListEqual(sorted(size_dict.keys()), ['char_matrix', 'indices', 'levenshtein_tokens'])
        for size_dict in _COUNTRY_RESOURCES['countries']['trigrams'].values():
            self.assertListEqual(sorted(size_dict.keys()), ['indices', 'trigram_tokens'])

    def test_indices(self):
        """
        Check if the indices used to look up canonical names are all within range
        """
        add_country_resources()
        from text_scrubber.geo.resources import _COUNTRY_RESOURCES

        country_dict = _COUNTRY_RESOURCES['countries']
        max_idx = len(country_dict['canonical_names']) - 1
        self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                            for canonical_name_idx, idx in country_dict['cleaned_location_map'].values()))
        for size_dict in country_dict['levenshtein'].values():
            self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                                for canonical_name_idx, idx in size_dict['indices']))
        for size_dict in country_dict['trigrams'].values():
            self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                                for canonical_name_idx, idx in size_dict['indices']))

    def test_bounds(self):
        """
        Check if the shapes are all correct
        """
        add_country_resources()
        from text_scrubber.geo.resources import _COUNTRY_RESOURCES

        country_dict = _COUNTRY_RESOURCES['countries']
        for size_dict in country_dict['levenshtein'].values():
            self.assertEqual(len(size_dict['indices']), len(size_dict['levenshtein_tokens']))
            self.assertEqual(len(size_dict['indices']), size_dict['char_matrix'].shape[0])
        for size_dict in country_dict['trigrams'].values():
            self.assertEqual(len(size_dict['indices']), size_dict['trigram_tokens'].shape[0])


class AddRegionResourcesTest(unittest.TestCase):

    def test_structure(self):
        """
        We're not testing everything here, just the structure of the dictionary. The other parts are too much work to
        test and are by proxy tested in other tests
        """
        add_region_resources({'NL'})
        from text_scrubber.geo.resources import _REGION_RESOURCES

        self.assertListEqual(sorted(_REGION_RESOURCES.keys()), ['regions_per_country_code_map'])
        self.assertIsInstance(_REGION_RESOURCES['regions_per_country_code_map'], dict)

        self.assertIn('NL', _REGION_RESOURCES['regions_per_country_code_map'])
        self.assertListEqual(sorted(_REGION_RESOURCES['regions_per_country_code_map']['NL'].keys()),
                             ['canonical_names', 'cleaned_location_map', 'levenshtein', 'trigrams'])
        self.assertIsInstance(_REGION_RESOURCES['regions_per_country_code_map']['NL']['levenshtein'], dict)
        self.assertIsInstance(_REGION_RESOURCES['regions_per_country_code_map']['NL']['trigrams'], dict)
        for size_dict in _REGION_RESOURCES['regions_per_country_code_map']['NL']['levenshtein'].values():
            self.assertListEqual(sorted(size_dict.keys()), ['char_matrix', 'indices', 'levenshtein_tokens'])
        for size_dict in _REGION_RESOURCES['regions_per_country_code_map']['NL']['trigrams'].values():
            self.assertListEqual(sorted(size_dict.keys()), ['indices', 'trigram_tokens'])

    def test_indices(self):
        """
        Check if the indices used to look up canonical names are all within range
        """
        add_region_resources({'DE'})
        from text_scrubber.geo.resources import _REGION_RESOURCES

        region_dict = _REGION_RESOURCES['regions_per_country_code_map']['DE']
        max_idx = len(region_dict['canonical_names']) - 1
        self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                            for canonical_name_idx, idx in region_dict['cleaned_location_map'].values()))
        for size_dict in region_dict['levenshtein'].values():
            self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                                for canonical_name_idx, idx in size_dict['indices']))
        for size_dict in region_dict['trigrams'].values():
            self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                                for canonical_name_idx, idx in size_dict['indices']))

    def test_bounds(self):
        """
        Check if the shapes are all correct
        """
        add_region_resources({'BE'})
        from text_scrubber.geo.resources import _REGION_RESOURCES

        region_dict = _REGION_RESOURCES['regions_per_country_code_map']['BE']
        for size_dict in region_dict['levenshtein'].values():
            self.assertEqual(len(size_dict['indices']), len(size_dict['levenshtein_tokens']))
            self.assertEqual(len(size_dict['indices']), size_dict['char_matrix'].shape[0])
        for size_dict in region_dict['trigrams'].values():
            self.assertEqual(len(size_dict['indices']), size_dict['trigram_tokens'].shape[0])


class AddCityResourcesTest(unittest.TestCase):

    def test_structure(self):
        """
        We're not testing everything here, just the structure of the dictionary. The other parts are too much work to
        test and are by proxy tested in other tests
        """
        add_city_resources({'NL'})
        from text_scrubber.geo.resources import _CITY_RESOURCES

        self.assertListEqual(sorted(_CITY_RESOURCES.keys()), ['cities_per_country_code_map'])
        self.assertIsInstance(_CITY_RESOURCES['cities_per_country_code_map'], dict)

        self.assertIn('NL', _CITY_RESOURCES['cities_per_country_code_map'])
        self.assertListEqual(sorted(_CITY_RESOURCES['cities_per_country_code_map']['NL'].keys()),
                             ['canonical_names', 'cleaned_location_map', 'levenshtein', 'trigrams'])
        self.assertIsInstance(_CITY_RESOURCES['cities_per_country_code_map']['NL']['levenshtein'], dict)
        self.assertIsInstance(_CITY_RESOURCES['cities_per_country_code_map']['NL']['trigrams'], dict)
        for size_dict in _CITY_RESOURCES['cities_per_country_code_map']['NL']['levenshtein'].values():
            self.assertListEqual(sorted(size_dict.keys()), ['char_matrix', 'indices', 'levenshtein_tokens'])
        for size_dict in _CITY_RESOURCES['cities_per_country_code_map']['NL']['trigrams'].values():
            self.assertListEqual(sorted(size_dict.keys()), ['indices', 'trigram_tokens'])

    def test_indices(self):
        """
        Check if the indices used to look up canonical names are all within range
        """
        add_city_resources({'DE'})
        from text_scrubber.geo.resources import _CITY_RESOURCES

        city_dict = _CITY_RESOURCES['cities_per_country_code_map']['DE']
        max_idx = len(city_dict['canonical_names']) - 1
        self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                            for canonical_name_idx, idx in city_dict['cleaned_location_map'].values()))
        for size_dict in city_dict['levenshtein'].values():
            self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                                for canonical_name_idx, idx in size_dict['indices']))
        for size_dict in city_dict['trigrams'].values():
            self.assertTrue(all(0 <= idx <= max_idx and 0 <= canonical_name_idx <= max_idx
                                for canonical_name_idx, idx in size_dict['indices']))

    def test_bounds(self):
        """
        Check if the shapes are all correct
        """
        add_city_resources({'BE'})
        from text_scrubber.geo.resources import _CITY_RESOURCES

        city_dict = _CITY_RESOURCES['cities_per_country_code_map']['BE']
        for size_dict in city_dict['levenshtein'].values():
            self.assertEqual(len(size_dict['indices']), len(size_dict['levenshtein_tokens']))
            self.assertEqual(len(size_dict['indices']), size_dict['char_matrix'].shape[0])
        for size_dict in city_dict['trigrams'].values():
            self.assertEqual(len(size_dict['indices']), size_dict['trigram_tokens'].shape[0])
