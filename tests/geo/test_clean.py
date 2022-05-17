import unittest

from text_scrubber.geo.clean import _clean_geo_string


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
