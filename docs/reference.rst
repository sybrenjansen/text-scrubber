API reference
=============

.. contents:: Contents
    :depth: 1
    :local:


TextScrubber
------------

.. autoclass:: text_scrubber.text_scrubber.TextScrubber
    :members:
    :special-members:


Geo
---

Normalization
~~~~~~~~~~~~~

.. autofunction:: text_scrubber.geo.normalize_country

.. autofunction:: text_scrubber.geo.normalize_region

.. autofunction:: text_scrubber.geo.normalize_city

.. autofunction:: text_scrubber.geo.normalize_country_to_country_codes

Cleaning
~~~~~~~~

.. autofunction:: text_scrubber.geo.clean_country

.. autofunction:: text_scrubber.geo.clean_region

.. autofunction:: text_scrubber.geo.clean_city

Finding locations within large strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: text_scrubber.geo.find_country_in_string

.. autofunction:: text_scrubber.geo.find_region_in_string

.. autofunction:: text_scrubber.geo.find_city_in_string

Resources
~~~~~~~~~

.. autofunction:: text_scrubber.geo.add_city_resources

.. autofunction:: text_scrubber.geo.add_region_resources
