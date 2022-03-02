Change log
==========

Master
------
- :meth:`text_scrubber.geo.normalize_country`, :meth:`text_scrubber.geo.normalize_state`, and
  :meth:`text_scrubber.geo.normalize_city` now optionally return the match scores
- Fixed replacement patterns for normalizing countries
- Few entries in country mapping updated
0.2.1
-----
*(2022-03-02)*
- Information about the cities in a country is loaded on the fly.

0.2.0
-----

*(2021-05-10)*

- Replaced `unidecode` by `anyascii`, which has a more relaxed license. Output of `to_ascii` can change because of it

0.1.1
-----

*(2020-09-10)*

- Removed Python 3.5 support

0.1.0
-----

*(2020-09-10)*

- First release
