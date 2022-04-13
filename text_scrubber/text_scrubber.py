import re
from functools import partial
from itertools import filterfalse
from operator import itemgetter
from string import punctuation
from typing import Callable, Generator, Iterable, Match, Pattern, Union, Dict, Set

from anyascii import anyascii
from num2words import num2words

from text_scrubber.io import read_resource_file

WholeText = str
Token = str
TokenizedText = Iterable[Token]
AnyText = Union[WholeText, TokenizedText]

# Precompile some regex objects
RE_TOKENIZE = re.compile(r'[.,!?:;*\-()\[\]\s_\\/]+')
RE_STRIP_QUOTES = re.compile(r'"|\'')
RE_FIND_DIGIT = re.compile(r'\d+')

# Read in a list of stop words
STOP_WORDS = set(read_resource_file(__file__, 'resources/stopwords.txt'))

# The Greek alphabet
TOKEN_MAP_GREEK = {'Α': 'Alpha', 'α': 'alpha', 'Β': 'Beta', 'β': 'beta', 'Γ': 'Gamma', 'γ': 'gamma', 'Δ': 'Delta',
                   'δ': 'delta', 'Ε': 'Epsilon', 'ε': 'epsilon', 'Ζ': 'Zeta', 'ζ': 'zeta', 'Η': 'Eta', 'η': 'eta',
                   'Θ': 'Theta', 'θ': 'theta', 'Ι': 'Iota', 'ι': 'ia', 'Κ': 'Kappa', 'κ': 'kappa', 'Λ': 'Lambda',
                   'λ': 'lambda', 'Μ': 'Mu', 'μ': 'mu', 'Ν': 'Nu', 'ν': 'nu', 'Ξ': 'Xi', 'ξ': 'xi', 'Ο': 'Omicron',
                   'ο': 'omicron', 'Π': 'Pi', 'π': 'pi', 'Ρ': 'Rho', 'ρ': 'rho', 'Σ': 'Sigma', 'σ': 'sigma',
                   'ς': 'sigma', 'Ϲ': 'Sigma', 'ϲ': 'sigma', 'Τ': 'Tau', 'τ': 'tau', 'Υ': 'Upsilon', 'υ': 'upsilon',
                   'Φ': 'Phi', 'φ': 'phi', 'Χ': 'Chi', 'χ': 'chi', 'Ψ': 'Psi', 'ψ': 'psi', 'Ω': 'Omega', 'ω': 'omega'}


class TextTransformer:

    def __init__(self, operation) -> None:
        """
        :param operation: A callable that is used to preprocess the text.
        """
        self.operation = operation

    def transform(self, X) -> Generator:
        return (self.operation(x) for x in X)


class TokenTransformer(TextTransformer):

    def __init__(self, operation) -> None:
        """
        :param operation: A callable that is used to preprocess a single token.
        """
        super().__init__(lambda X: [operation(x) for x in X])


class TextScrubber:
    """
    Cleans a single or a collection of strings.

    Can be easily constructed and configured with building blocks::

        ts = (TextScrubber().lowercase()
                             .strip_accents()
                             .tokenize()
                             .remove_stop_words()
                             .join())
    """

    def __init__(self) -> None:
        # Initialize empty pipeline
        self.cleaner = []

    def _add_step(self, name: str, func: Callable, on_tokens: bool) -> 'TextScrubber':
        """
        Adds a single step to the pipeline.

        :param name: Name of the step.
        :param func: Callable function/object which performs a transformation.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        """
        transformer = TokenTransformer(func) if on_tokens else TextTransformer(func)
        self.cleaner.append(('{}_{}'.format(name, len(self.cleaner)), transformer))
        return self

    def text_transform(self, func: Callable[[AnyText], AnyText], name: str = 'string_transform') -> 'TextScrubber':
        """
        Adds a function operating on texts to the pipeline.

        :param func: Function to perform on whole strings.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, func, False)

    def token_transform(self, func: Callable[[Token], Token], name: str = 'token_transform') -> 'TextScrubber':
        """
        Adds a function operating on tokens to the pipeline.

        :param func: Function to perform on each token.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, func, True)

    def transform(self, s: Union[AnyText, Iterable[AnyText]], on_tokens: bool = False,
                  to_set: bool = False) -> Union[AnyText, Iterable[AnyText]]:
        """
        Transform a single or multiple strings.

        :param s: One or multiple texts, which can either be tokenized or not.
        :param on_tokens: Whether to treat the iterable of strings as tokens or complete strings.
        :param to_set: Whether to return a set instead of a list when an iterable of strings is provided.
        :return: Cleaned string or set of cleaned strings.
        """
        if on_tokens or isinstance(s, (str, bytes)):
            return next(iter(self._transform((s,))))
        else:
            cleaned_s = self._transform(s)
            return set(cleaned_s) if to_set else list(cleaned_s)

    def transform_generator(self, s: Iterable[AnyText]) -> Generator[AnyText, None, None]:
        """
        Transform multiple strings and receive a generator as result.

        :param s: Iterable of strings.
        :return: Generator of cleaned strings.
        """
        yield from self._transform(s)

    def _transform(self, s: Iterable[AnyText]) -> Iterable[AnyText]:
        """
        Calls the entire cleaning pipeline on the iterable of strings.

        :param s: Iterable of strings to transform.
        :return: Cleaned string.
        """
        for _, transform in self.cleaner:
            s = transform.transform(s)
        return s

    def __repr__(self) -> str:
        """
        Displays the cleaning pipeline.
        """
        return f"{__name__}({' -> '.join(name for name, _ in self.cleaner)})"

    __str__ = __repr__

    ##################
    # Building blocks
    ##################

    def filter_tokens(self, test: Callable[[Token], bool] = lambda t: t, neg: bool = False,
                      name: str = 'filter_tokens') -> 'TextScrubber':
        """
        Filter tokens given a certain test.

        :param test: Function which should return ``False`` when a token should be removed.
        :param neg: Whether the test should be reversed.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, partial(filterfalse if neg else filter, test), on_tokens=False)

    def initials(self, name: str = 'initials') -> 'TextScrubber':
        """
        Removes all, but the first element of a text or tokens.

        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, itemgetter(0), on_tokens=True)

    def join(self, sep: str = ' ', on_tokens: bool = False, name: str = 'join') -> 'TextScrubber':
        """
        Joins elements to a single string.

        :param sep: Separator to join tokens.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, sep.join, on_tokens=on_tokens)

    def lowercase(self, on_tokens: bool = False, name: str = 'lowercase') -> 'TextScrubber':
        """
        Lowercases text or tokens.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, str.lower, on_tokens)

    def num2words(self, include_commas: bool = False, language: str = 'en', on_tokens: bool = False,
                  name: str = 'num2words') -> 'TextScrubber':
        """
        Converts numbers like ``42`` to words like ``forty-two``. See https://github.com/savoirfairelinux/num2words.

        :param include_commas: Whether to let num2words include commas for more natural reading.
        :param language: The language in which to convert the number (see num2words documentation for possible values).
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        def _transform(s):
            words = []
            for word in s.split():
                # Split word at digit positions (if any), remove leading and trailing empty parts
                digits_span = [0] + [idx for m in RE_FIND_DIGIT.finditer(word) for idx in m.span()] + [None]
                tokens = (word[digits_span[i]:digits_span[i + 1]] for i in range(len(digits_span) - 1))
                tokens = (token for token in tokens if len(token))

                # Try to parse the token in to a number. If it succeeds, convert to text. If not, do not convert
                for token in tokens:
                    try:
                        num_words = num2words(int(token), lang=language)
                        words.append(num_words if include_commas else num_words.replace(',', ''))
                    except ValueError:
                        words.append(token)

            return ' '.join(words)

        return self._add_step(name, _transform, on_tokens=on_tokens)

    def remove_digits(self, on_tokens: bool = False, name: str = 'remove_digits') -> 'TextScrubber':
        """
        Removes digits from text or tokens.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, lambda t: ''.join(char for char in t if not char.isdigit()), on_tokens)

    def remove_excessive_whitespace(self, on_tokens: bool = False,
                                    name: str = 'strip_excessive_whitespace') -> 'TextScrubber':
        """
        Replaces multi-character whitespace with a single whitespace.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, lambda t: ' '.join(t.split()), on_tokens)

    def remove_html_tags(self, on_tokens: bool = False, name: str = 'remove_html_tags') -> 'TextScrubber':
        """
        Removes all HTML tags (i.e., everything that matches ``r'<.*?>'``).

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self.sub(r'<.*?>', '', on_tokens=on_tokens, name=name)

    def removes_prefixes(self, prefixes: Set[str], on_tokens: bool = False,
                         name: str = 'strip_prefix') -> 'TextScrubber':
        """
        Removes a set of prefixes.

        :param prefixes: Set of prefixes to remove.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self.sub(rf"^{'|^'.join(prefixes)}", '', on_tokens=on_tokens, name=name)

    def remove_punctuation(self, keep_punctuation: str = '', on_tokens: bool = False,
                           name: str = 'remove_punctuation') -> 'TextScrubber':
        """
        Removes all, but the provided punctuation from text or tokens.

        :param keep_punctuation: A string containing the punctuation-tokens that should NOT be removed.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        cleanup_table = {ord(punct): None for punct in punctuation if punct not in keep_punctuation}
        remove_func = partial(_remove_punctuation, cleanup_table=cleanup_table)
        return self._add_step(name, remove_func, on_tokens=on_tokens)

    def remove_quotes(self, on_tokens: bool = False, name: str = 'strip_quotes') -> 'TextScrubber':
        """
        Removes single and double quotes from text or tokens.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, lambda t: RE_STRIP_QUOTES.sub('', t), on_tokens)

    def remove_stop_words(self, stop_words: Iterable[str] = None, name: str = 'remove_stop_words',
                          case_sensitive: bool = False) -> 'TextScrubber':
        """
        Removes stop words. All-caps tokens are considered to be abbreviations and are retained.

        :param case_sensitive: should the stopword removal be case_sensitive or not
        :param stop_words: Iterable of stop words to remove. If not provided it will use a default list of stop words.
        :param name: Name to give to the pipeline step.
        """
        stop_words_set = set(stop_words) if stop_words else STOP_WORDS
        if not case_sensitive:
            remove_func = partial(filter, lambda t: t.isupper() or t.lower() not in stop_words_set)
        else:
            remove_func = partial(filter, lambda t: t.isupper() or t not in stop_words_set)
        return self._add_step(name, remove_func, on_tokens=False)

    def remove_suffixes(self, suffixes: Set[str], on_tokens: bool = False,
                        name: str = 'strip_suffix') -> 'TextScrubber':
        """
        Removes a set of suffixes.

        :param suffixes: Set of suffixes to remove.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self.sub(rf"{'$|'.join(suffixes)}$", '', on_tokens=on_tokens, name=name)

    def sort(self, reverse: bool = False, on_tokens: bool = False, name: str = 'sort') -> 'TextScrubber':
        """
        Sort text or tokens.

        :param reverse: Reverse sort.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, lambda tokens: sorted(tokens, reverse=reverse), on_tokens=on_tokens)

    def strip(self, chars: str = None, on_tokens: bool = False, name: str = 'strip') -> 'TextScrubber':
        """
        Uses the builtin ``str.strip`` function to strip leading/trailing characters from text or tokens.

        :param chars: If chars is given and not None, remove leading/trailing characters in chars instead of whitespace.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        strip_func = str.strip if chars is None else lambda s: s.strip(chars)
        return self._add_step(name, strip_func, on_tokens)

    def sub(self, search: Union[str, Pattern], replace: Union[str, Callable[[Match[str]], str]],
            on_tokens: bool = False, name: str = 'sub') -> 'TextScrubber':
        """
        Replace all occurrences of a search query with a replacement string.

        :param search: String or regex on which to match.
        :param replace: Replacement string or callable for matched groups.
        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        search_re = re.compile(search)
        sub_func = partial(search_re.sub, replace)
        return self._add_step(name, sub_func, on_tokens=on_tokens)

    def sub_greek_chars(self, on_tokens: bool = False, name: str = 'sub_greek_chars') -> 'TextScrubber':
        """
        Replace Greek characters with their English name. E.g., ``α`` is replaced by ``alpha``.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, lambda t: ''.join(TOKEN_MAP_GREEK.get(c, c) for c in t), on_tokens=on_tokens)

    def sub_html_chars(self, on_tokens: bool = False, name: str = 'sub_html_chars') -> 'TextScrubber':
        """
        Match HTML char encodings such as ``&#410;`` and replaces them with the equivalent unicode character.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self.sub(r'&#(\d{1,3});', lambda m: chr(int(m.group(1))), on_tokens=on_tokens, name=name)

    def sub_latex_chars(self, on_tokens: bool = False, name: str = 'sub_latex_chars') -> 'TextScrubber':
        r"""
        Match accented LaTeX commands such as ``\"{o}`` and ``\^{\i}`` OR match direct commands such as ``\o`` and
        ``\l{}`` and ``{\L}``, and keep only the regular ascii character.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        latex_re = r"\\[Hhckbdruvt'\"~`^=.]{?\\?([a-zA-Z]+)}?|{?\\([LlOoIiJj]{1})}?{?}?"
        return self.sub(latex_re, lambda m: m.group(2) or m.group(1), on_tokens=on_tokens, name=name)

    def sub_tokens(self, func: Callable[[Token], Token], name: str = 'substitute_tokens') -> 'TextScrubber':
        """
        Substitutes tokens.

        :param func: Function that substitutes tokens.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, func, on_tokens=True)

    def to_ascii(self, on_tokens: bool = False, name: str = 'to_ascii') -> 'TextScrubber':
        """
        Uses ``anyascii`` to strip accents and convert unicode characters to plain 7-bit ASCII.

        :param on_tokens: Whether to transform on a list of tokens or a single string.
        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, anyascii, on_tokens)

    # Alias
    strip_accents = to_ascii

    def to_list(self, name: str = 'to_list') -> 'TextScrubber':
        """
        Converts the iterable of tokens to a list (useful when not joining as you're otherwise left with generator or
        ``filter`` objects which still need to be evaluated).

        :param name: Name to give to the pipeline step.
        """
        return self._add_step(name, list, on_tokens=False)

    def tokenize(self, func: Callable[[WholeText], TokenizedText] = None, name: str = 'tokenize') -> 'TextScrubber':
        """
        Tokenizes a text.

        :param func: Function used for tokenizing a string. None to use the default tokenizer.
        :param name: Name to give to the pipeline step.
        """
        func = func if func is not None else lambda s: RE_TOKENIZE.split(s)
        return self._add_step(name, func, False)


def _remove_punctuation(text: str, cleanup_table: Dict[int, None]) -> str:
    """
    Removes punctuation from a text given a cleanup table.

    :param text: String to clean.
    :param cleanup_table: Translation tabel mapping punctuation ordinals to None.
    :return: Cleaned string.
    """
    return text.translate(cleanup_table)
