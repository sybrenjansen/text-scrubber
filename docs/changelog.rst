Change log
==========

0.3.0
-----

*(2022-04-13)*

- Renamed `normalize_state` to :meth:`text_scrubber.geo.normalize_region`, as it now handles all kinds of regions
- Expanded countries, regions, and cities with geonames database, increasing the completeness of the geo database
- :meth:`text_scrubber.geo.normalize_country`, :meth:`text_scrubber.geo.normalize_region`, and
  :meth:`text_scrubber.geo.normalize_city` now return the match scores as well
- :meth:`text_scrubber.geo.normalize_region` and :meth:`text_scrubber.geo.normalize_city` also return the corresponding
  normalized country
- Added :meth:`text_scrubber.geo.find_country_in_string`, :meth:`text_scrubber.geo.find_city_in_string`, and
  :meth:`text_scrubber.geo.find_region_in_string` functions that find a location in a string
- Updated cleaning pipeline of :meth:`text_scrubber.geo.clean_country`, :meth:`text_scrubber.geo.clean_city`, and
  :meth:`text_scrubber.geo.clean_region`
- Added ``case_sensitive`` boolean flag to :meth:`text_scrubber.text_scrubber.TextScrubber.remove_stop_words`
- Improved speed of trigram matching by mapping trigrams to integer indices

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
