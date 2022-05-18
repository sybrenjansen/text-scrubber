import types
import unittest

from text_scrubber import TextScrubber


class TextScrubberTest(unittest.TestCase):

    def test_text_transform(self):
        sc = TextScrubber().text_transform(func=lambda s: s.capitalize())
        self.assertEqual(sc.transform('hello world'), 'Hello world')
        self.assertEqual(sc.transform(['hello world', 'slimmer AI']), ['Hello world', 'Slimmer ai'])

    def test_token_transform(self):
        # We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().token_transform(func=lambda t: t.capitalize()).to_list()
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), ['Hello', 'World'])
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]), [['Hello', 'World'], ['Slimmer', 'Ai']])

    def test_transform(self):
        # The following will work with tokenizing
        sc = (TextScrubber().tokenize().initials().join(''))
        self.assertEqual(sc.transform('hello world', on_tokens=False, to_set=False), 'hw')
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=False, to_set=False), ['h', 'w'])
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=False, to_set=True), {'h', 'w'})
        self.assertEqual(sc.transform(['hello world', 'slimmer AI'], on_tokens=False, to_set=True), {'hw', 'sA'})

        # Will fail because we're dealing with tokens and we can't tokenize lists
        with self.assertRaises(TypeError):
            sc.transform(['hello world', 'slimmer AI'], on_tokens=True, to_set=True)
        with self.assertRaises(TypeError):
            sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=True, to_set=False)
        with self.assertRaises(TypeError):
            sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=False, to_set=False)

        # The following will work without tokenizing
        sc = (TextScrubber().initials().join(''))
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=False, to_set=False), ['hello', 'world'])
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True, to_set=False), 'hw')
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=False, to_set=False),
                         ['hw', 'sA'])
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=False, to_set=True),
                         {'hw', 'sA'})
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=True, to_set=False),
                         'helloslimmer')

    def test_transform_generator(self):
        sc = (TextScrubber().tokenize().initials().join(''))
        gen = sc.transform_generator(['hello world', 'slimmer AI'])
        self.assertTrue(isinstance(gen, types.GeneratorType))
        self.assertEqual(list(gen), ['hw', 'sA'])

    def test_filter_tokens(self):
        # Default test
        sc = TextScrubber().filter_tokens(test=lambda t: t, neg=False).to_list()
        self.assertEqual(sc.transform(['hello', '', 'world'], on_tokens=True), ['hello', 'world'])
        self.assertEqual(sc.transform([['hello', '', 'world'], [None, 'slimmer', 'AI', False]]),
                         [['hello', 'world'], ['slimmer', 'AI']])

        # Default test using negative results
        sc = TextScrubber().filter_tokens(test=lambda t: t, neg=True).to_list()
        self.assertEqual(sc.transform(['hello', '', 'world'], on_tokens=True), [''])
        self.assertEqual(sc.transform([['hello', '', 'world'], [None, 'slimmer', 'AI', False]]), [[''], [None, False]])

        # Custom test
        sc = TextScrubber().filter_tokens(test=lambda t: isinstance(t, str) and t.islower(), neg=False).to_list()
        self.assertEqual(sc.transform(['hello', '', 'world'], on_tokens=True), ['hello', 'world'])
        self.assertEqual(sc.transform([['hello', '', 'world'], [None, 'slimmer', 'AI', False]]),
                         [['hello', 'world'], ['slimmer']])

    def test_initials(self):
        # We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().initials().to_list()
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), ['h', 'w'])
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]), [['h', 'w'], ['s', 'A']])

    def test_join(self):
        # Default separator
        sc = TextScrubber().join(sep=' ')
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), 'hello world')
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]), ['hello world', 'slimmer AI'])

        # Custom separator
        sc = TextScrubber().join(sep=' & ')
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), 'hello & world')
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]), ['hello & world', 'slimmer & AI'])

    def test_lowercase(self):
        # On entire strings
        sc = TextScrubber().lowercase(on_tokens=False)
        self.assertEqual(sc.transform('Hello World'), 'hello world')
        self.assertEqual(sc.transform(['Hello World', 'slimmer AI']), ['hello world', 'slimmer ai'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().lowercase(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['Hello World'], on_tokens=True), ['hello world'])
        self.assertEqual(sc.transform([['Hello World', 'slimmer AI']]), [['hello world', 'slimmer ai']])

    def test_num2words(self):
        # Default settings. On strings
        sc = TextScrubber().num2words(include_commas=False, on_tokens=False)
        self.assertEqual(sc.transform('hello 1337 world'), 'hello one thousand three hundred and thirty-seven world')
        self.assertEqual(sc.transform(['hello 1337 world', 'Atoomweg 6b']),
                         ['hello one thousand three hundred and thirty-seven world', 'Atoomweg six b'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().num2words(include_commas=False, on_tokens=True).to_list()
        self.assertEqual(sc.transform(['hello', '1337', 'world'], on_tokens=True),
                         ['hello', 'one thousand three hundred and thirty-seven', 'world'])
        self.assertEqual(sc.transform([['hello', '1337', 'world'], ['Atoomweg', '6b']]),
                         [['hello', 'one thousand three hundred and thirty-seven',  'world'], ['Atoomweg', 'six b']])

        # Including commas
        sc = TextScrubber().num2words(include_commas=True, on_tokens=False)
        self.assertEqual(sc.transform('hello 1337 world'), 'hello one thousand, three hundred and thirty-seven world')
        self.assertEqual(sc.transform(['hello 1337 world', 'Atoomweg 6b']),
                         ['hello one thousand, three hundred and thirty-seven world', 'Atoomweg six b'])

        # Different language
        sc = TextScrubber().num2words(include_commas=False, language='nl', on_tokens=False)
        self.assertEqual(sc.transform('hello 1337 world'), 'hello duizenddriehonderdzevenendertig world')
        self.assertEqual(sc.transform(['hello 1337 world', 'Atoomweg 6b']),
                         ['hello duizenddriehonderdzevenendertig world', 'Atoomweg zes b'])

    def test_remove_digits(self):
        # On entire strings
        sc = TextScrubber().remove_digits(on_tokens=False)
        self.assertEqual(sc.transform('hell0 world12'), 'hell world')
        self.assertEqual(sc.transform(['hell0 world12', 'sl1mm3r A1']), ['hell world', 'slmmr A'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_digits(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['hell0 world12'], on_tokens=True), ['hell world'])
        self.assertEqual(sc.transform([['hell0 world12', 'sl1mm3r A1']]), [['hell world', 'slmmr A']])

    def test_remove_excessive_whitespace(self):
        # On entire strings
        sc = TextScrubber().remove_excessive_whitespace(on_tokens=False)
        self.assertEqual(sc.transform('hello  world '), 'hello world')
        self.assertEqual(sc.transform(['hello   world ', ' slimmer  AI ']), ['hello world', 'slimmer AI'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_excessive_whitespace(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['hello ', 'wor ld'], on_tokens=True), ['hello', 'wor ld'])

    def test_remove_html_tags(self):
        # On entire strings
        sc = TextScrubber().remove_html_tags(on_tokens=False)
        self.assertEqual(sc.transform('<b>hello</b> wo<FOO>rld'), 'hello world')
        self.assertEqual(sc.transform(['hello <i>world</i></br>', '<a tag>slimmer</some tag><sup>AI</sup>']),
                         ['hello world', 'slimmerAI'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_html_tags(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['<b>hello</b> wo<FOO>rld'], on_tokens=True), ['hello world'])
        self.assertEqual(sc.transform([['hello <i>world</i></br>', '<a tag>slimmer</some tag><sup>AI</sup>']]),
                         [['hello world', 'slimmerAI']])

    def test_remove_prefixes(self):
        # On entire strings
        sc = TextScrubber().removes_prefixes({'foo', 'world'}, on_tokens=False)
        self.assertEqual(sc.transform('fooBar fooBar'), 'Bar fooBar')
        self.assertEqual(sc.transform(['hello world', 'world hello']), ['hello world', ' hello'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().removes_prefixes({'foo', 'world'}, on_tokens=True)
        self.assertEqual(sc.transform(['fooBar fooBar'], on_tokens=True), ['Bar fooBar'])
        self.assertEqual(sc.transform([['hello world', 'world hello']]), [['hello world', ' hello']])

    def test_remove_punctuation(self):
        # On entire strings
        sc = TextScrubber().remove_punctuation(keep_punctuation='', on_tokens=False)
        self.assertEqual(sc.transform('hello, world!'), 'hello world')
        self.assertEqual(sc.transform(['hello, world!', 'slimmer-slimst.Ai']), ['hello world', 'slimmerslimstAi'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_punctuation(keep_punctuation='', on_tokens=True).to_list()
        self.assertEqual(sc.transform(['hello, world!'], on_tokens=True), ['hello world'])
        self.assertEqual(sc.transform([['hello, world!', 'slimmer-slimst.Ai']]), [['hello world', 'slimmerslimstAi']])

        # With a custom list of punctuation to keep
        sc = TextScrubber().remove_punctuation(keep_punctuation=',.', on_tokens=False)
        self.assertEqual(sc.transform('hello, world!'), 'hello, world')
        self.assertEqual(sc.transform(['hello, world!', 'slimmer-slimst.Ai']), ['hello, world', 'slimmerslimst.Ai'])

    def test_remove_quotes(self):
        # On entire strings
        sc = TextScrubber().remove_quotes(on_tokens=False)
        self.assertEqual(sc.transform('"hello world"'), 'hello world')
        self.assertEqual(sc.transform(['"hello world"', 'slimmer\' AI']), ['hello world', 'slimmer AI'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_quotes(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['"hello world"'], on_tokens=True), ['hello world'])
        self.assertEqual(sc.transform([['"hello world"', 'slimmer\' AI']]), [['hello world', 'slimmer AI']])

    def test_remove_stop_words(self):
        # Default stop words. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_stop_words(stop_words=None).to_list()
        self.assertEqual(sc.transform(['around', 'the', 'world'], on_tokens=True), ['world'])
        self.assertEqual(sc.transform([['around', 'the', 'world'], ['once', 'upon', 'a', 'time']]),
                         [['world'], ['time']])

        # Custom stop words. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_stop_words(stop_words={'world', 'time'}).to_list()
        self.assertEqual(sc.transform(['around', 'the', 'world'], on_tokens=True), ['around', 'the'])
        self.assertEqual(sc.transform([['around', 'the', 'world'], ['once', 'upon', 'a', 'time']]),
                         [['around', 'the'], ['once', 'upon', 'a']])

        # All caps words shouldn't be removed
        sc = TextScrubber().remove_stop_words(stop_words=None).to_list()
        self.assertEqual(sc.transform(['around', 'THE', 'world'], on_tokens=True), ['THE', 'world'])
        self.assertEqual(sc.transform([['AROUND', 'the', 'world'], ['once', 'upon', 'A', 'time']]),
                         [['AROUND', 'world'], ['A', 'time']])

    def test_remove_suffixes(self):
        # On entire strings
        sc = TextScrubber().remove_suffixes({'Bar', 'world'}, on_tokens=False)
        self.assertEqual(sc.transform('fooBar fooBar'), 'fooBar foo')
        self.assertEqual(sc.transform(['hello world', 'world hello']), ['hello ', 'world hello'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().remove_suffixes({'Bar', 'world'}, on_tokens=True)
        self.assertEqual(sc.transform(['fooBar fooBar'], on_tokens=True), ['fooBar foo'])
        self.assertEqual(sc.transform([['hello world', 'world hello']]), [['hello ', 'world hello']])

    def test_sort(self):
        # Default setting. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sort(reverse=False).to_list()
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), ['hello', 'world'])
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]), [['hello', 'world'], ['AI', 'slimmer']])

        # Reverse order. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sort(reverse=True).to_list()
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), ['world', 'hello'])
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]), [['world', 'hello'], ['slimmer', 'AI']])

        # Sort on tokens
        sc = TextScrubber().sort(reverse=True, on_tokens=False).to_list()
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=True),
                         [['slimmer', 'AI'], ['hello', 'world']])
        sc = TextScrubber().sort(reverse=True, on_tokens=True).to_list()
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']], on_tokens=True),
                         [['world', 'hello'], ['slimmer', 'AI']])

    def test_strip(self):
        # On entire strings
        sc = TextScrubber().strip(chars=None, on_tokens=False)
        self.assertEqual(sc.transform('  hello   world'), 'hello   world')
        self.assertEqual(sc.transform(['  hello    world', 'slimmer AI  ']), ['hello    world', 'slimmer AI'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().strip(chars=None, on_tokens=True).to_list()
        self.assertEqual(sc.transform(['  hello   world'], on_tokens=True), ['hello   world'])
        self.assertEqual(sc.transform([['  hello    world', 'slimmer AI  ']]), [['hello    world', 'slimmer AI']])

        # With custom chars
        sc = TextScrubber().strip(chars='ld', on_tokens=False)
        self.assertEqual(sc.transform('  hello   world'), '  hello   wor')
        self.assertEqual(sc.transform(['  hello    world', 'slimmer AI  ']), ['  hello    wor', 'slimmer AI  '])

    def test_sub(self):
        # Substitute with string on entire string.
        sc = TextScrubber().sub(search='big', replace='small')
        self.assertEqual(sc.transform('hello big world.'), 'hello small world.')

        # Substitute with string on tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sub(search='big', replace='small', on_tokens=True).to_list()
        self.assertEqual(sc.transform(['hello', 'big', 'world'], on_tokens=True), ['hello', 'small', 'world'])
        self.assertEqual(sc.transform([['hello', 'big', 'world']]), [['hello', 'small', 'world']])

        # Substitute with regex on entire string.
        sc = TextScrubber().sub(search=r'ph\.?\ ?d\.?', replace='phd')
        self.assertEqual(sc.transform('i have a ph.d. in banana pies'), 'i have a phd in banana pies')

        # Substitute with regex on tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sub(search=r'ph\.?\ ?d\.?', replace='phd', on_tokens=True).to_list()
        self.assertEqual(sc.transform(['i', 'am', 'phd.', 'student.'], on_tokens=True), ['i', 'am', 'phd', 'student.'])
        self.assertEqual(sc.transform([['i', 'am', 'phd.', 'student.']]), [['i', 'am', 'phd', 'student.']])

    def test_sub_greek_chars(self):
        # On entire string.
        sc = TextScrubber().sub_greek_chars()
        self.assertEqual(sc.transform('α * β^Λ'), 'alpha * beta^Lambda')

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sub_greek_chars(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['α * β^Λ', 'χΥΖ'], on_tokens=True), ['alpha * beta^Lambda', 'chiUpsilonZeta'])

    def test_sub_html_chars(self):
        # On entire string.
        sc = TextScrubber().sub_html_chars()
        self.assertEqual(sc.transform('Eric Zei&#223;ner'), 'Eric Zeißner')
        self.assertEqual(sc.transform('Marco P&#246;chacker'), 'Marco Pöchacker')
        self.assertEqual(sc.transform('&#64; My Place'), '@ My Place')
        self.assertEqual(sc.transform('Carl&#39;s'), 'Carl\'s')

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sub_html_chars(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['Marco', 'P&#246;chacker'], on_tokens=True), ['Marco', 'Pöchacker'])

    def test_sub_latex_chars(self):
        # On entire string.
        sc = TextScrubber().sub_latex_chars()
        self.assertEqual(sc.transform(r'Eric \"Ozg\"ur Sar{\i}o\u{g}lu'), 'Eric Ozgur Sarioglu')
        self.assertEqual(sc.transform(r'Jan K\v{r}et\'insk\'y'), 'Jan Kretinsky')

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sub_latex_chars(on_tokens=True).to_list()
        self.assertEqual(sc.transform([r'Mieczys{\l}aw', r'K{\l}opotek'], on_tokens=True), ['Mieczyslaw', 'Klopotek'])

    def test_sub_tokens(self):
        # We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().sub_tokens(func=lambda t: {'hello': 'goodbye', 'AI': 'ML'}.get(t, t)).to_list()
        self.assertEqual(sc.transform(['hello', 'world'], on_tokens=True), ['goodbye', 'world'])
        self.assertEqual(sc.transform([['hello', 'world'], ['slimmer', 'AI']]),
                         [['goodbye', 'world'], ['slimmer', 'ML']])

    def test_to_ascii(self):
        # On entire strings
        sc = TextScrubber().to_ascii(on_tokens=False)
        self.assertEqual(sc.transform('héllô wòrld'), 'hello world')
        self.assertEqual(sc.transform(['héllô wòrld', 'slímm̀er ÀI']), ['hello world', 'slimmer AI'])

        # On tokens. We use a to_list() here such that we don't receive a generator
        sc = TextScrubber().to_ascii(on_tokens=True).to_list()
        self.assertEqual(sc.transform(['héllô wòrld'], on_tokens=True), ['hello world'])
        self.assertEqual(sc.transform([['héllô wòrld', 'slímm̀er ÀI']]), [['hello world', 'slimmer AI']])

    def test_to_list(self):
        # The map objects will be materialized by the to_list() function
        sc = TextScrubber().to_list()
        self.assertEqual(sc.transform(map(str.upper, ['hello', 'world']), on_tokens=True), ['HELLO', 'WORLD'])
        self.assertEqual(sc.transform([map(str.upper, ['hello', 'world']), map(str.upper, ['slimmer', 'Ai'])],
                                      to_set=False), [['HELLO', 'WORLD'], ['SLIMMER', 'AI']])

    def test_tokenize(self):
        # Using the default tokenizer
        sc = TextScrubber().tokenize()
        self.assertEqual(sc.transform('hello world'), ['hello', 'world'])
        self.assertEqual(sc.transform(['hello world', 'slimmer AI']), [['hello', 'world'], ['slimmer', 'AI']])

        # Using a custom one
        sc = TextScrubber().tokenize(func=lambda s: s.split('e'))
        self.assertEqual(sc.transform('hello world'), ['h', 'llo world'])
        self.assertEqual(sc.transform(['hello world', 'slimmer AI']), [['h', 'llo world'], ['slimm', 'r AI']])
