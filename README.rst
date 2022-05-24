text-scrubber
=============

|Build status| |Docs status|

.. |Build status| image:: https://github.com/Slimmer-AI/text-scrubber/workflows/Build/badge.svg?branch=master
.. |Docs status| image:: https://github.com/Slimmer-AI/text-scrubber/workflows/Docs/badge.svg?branch=master

``text-scrubber`` is a Python package that offers text scrubbing functionality, providing building blocks for string
cleaning as well as normalizing geographical text (countries/states/cities).

Full documentation is available at https://slimmer-ai.github.io/text-scrubber/.


TextScrubber
------------

The ``TextScrubber`` class cleans a single or a collection of strings. It can be easily constructed and configured with
building blocks:


.. code-block:: python

    from text_scrubber import TextScrubber

    ts = (TextScrubber().to_ascii()
                        .lowercase()
                        .tokenize()
                        .remove_stop_words()
                        .join())

which can then be used as:

.. code-block:: python

    ts.transform('héLlô there, WòrlD')  # outputs 'hello world'

or with an iterable of input:

.. code-block:: python

    ts.transform(['héLlô there, WòrlD', 'slímm̀er ÀI'])  # outputs ['hello world', 'slimmer AI']

For a complete list of building blocks please refer to the ``TextScrubber`` API reference.

Geo
---

The ``text_scrubber.geo`` module contains functions to normalize geographical data which deal with spelling errors,
country name variations, etc. In the output the ``NormalizedCountryMatch`` and ``NormalizedLocationMatch`` object names
have been replaced with ``Match`` to make the output more readable.

.. code-block:: python

    from text_scrubber.geo import normalize_country, normalize_region, normalize_city

    """
    Countries
    """

    normalize_country('Peoples rep. of China')
    # [Match(canonical_name='China', matched_name='Peoples Republic of China', score=1.0)]

    normalize_country('Deutschland')
    # [Match(canonical_name='Germany', matched_name='Deutschland', score=1.0)]

    normalize_country('st Nevis and Kitties')
    # [Match(canonical_name='Saint Kitts and Nevis', matched_name='Saint Kitts and Nevis',
    #        score=0.75)]

    normalize_country('ira')
    # [Match(canonical_name='Iran', matched_name='Iran', score=0.857),
    #  Match(canonical_name='Iraq', matched_name='Iraq', score=0.857)]

    """
    Cities
    """

    normalize_city('Leibnitz', ['Austria'])
    # [Match(canonical_name='Leibnitz', matched_name='Leibnitz', country='Austria', score=1.0)]

    normalize_city('heidelberg')
    # [Match(canonical_name='Heidelberg', matched_name='Heidelberg', country='Germany',
    #        score=1.0),
    #  Match(canonical_name='Heidelberg', matched_name='Heidelberg', country='South Africa',
    #        score=1.0),
    #  Match(canonical_name='Heidelberg', matched_name='Heidelberg', country='United States',
    #        score=1.0)]

    normalize_city('ohioo', ['US'])
    # [Match(canonical_name='Ohio', matched_name='Ohio', country='United States', score=0.889)]

    normalize_city('Madri', ['Spain', 'US', 'Brazil'])
    # [Match(canonical_name='Madrid', matched_name='Madrid', country='Spain', score=0.909),
    #  Match(canonical_name='Madrid', matched_name='Madrid', country='United States',
    #        score=0.909),
    #  Match(canonical_name='Mari', matched_name='Mari', country='Brazil', score=0.889)]

    """
    Regions
    """

    normalize_region('triangle park', ['US'])
    # [Match(canonical_name='The Triangle Park', matched_name='The Triangle Park',
    #        country='United States', score=1.0)]

    normalize_region('Fur', ['Denmark'])
    # [Match(canonical_name='Fur', matched_name='Fur', country='Denmark', score=1.0)]

    normalize_region('texel', ['NL'])
    # [Match(canonical_name='Texel', matched_name='Texel', country='Netherlands', score=1.0)]

Each of the above normalization functions return the canonical name, matched name, the match score, and when normalizing
cities or regions it will also contain the corresponding country. The difference between canonical and matched name
stems from the fact that some countries, cities, or regions can have alternative names. E.g., ``NYC`` maps to
``New York City``. When the query was ``NYCC`` the canonical name will be ``New York City``, but the matched name
``NYC``. The match scores are always between 0.0 and 1.0, where 1.0 is a perfect match. If a known mapping exists, like
``Deutschland`` to ``Germany``, then the match score will be 1.0.

The ``text_scrubber.geo`` module also contains functions to find the name of places (country, region, and city) in
text dealing with spelling errors, country name variations, etc.:

.. code-block:: python

    from text_scrubber.geo import (find_city_in_string, find_country_in_string,
                                   find_region_in_string)

    """
    Countries
    """

    find_country_in_string("Institute of German study, Accra, Ghana")
    # [CountryMatch(substring_range=(34, 39), substring='Ghana', canonical_name='Ghana',
    #               matched_name='Ghana', score=1.0),
    #  CountryMatch(substring_range=(13, 19), substring='German', canonical_name='Germany',
    #               matched_name='Germany', score=0.923)]

    find_country_in_string("Peking University, 5 Yiheyuan Rd, "
                           "Haidian District, Beijing, CH, 100871")
    # This was a trick question though, as CH=Switzerland. China is CN
    # [CountryMatch(substring_range=(61, 63), substring='CH', canonical_name='Switzerland',
    #               matched_name='CH', score=1.0)]

    """
    Cities
    """

    find_city_in_string("Météorage Pau France", {"France"})
    # [LocationMatch(substring_range=(10, 13), substring='Pau', canonical_name='Pau',
    #                matched_name='Pau', country='France', score=1.0),
    #  LocationMatch(substring_range=(14, 20), substring='France', canonical_name='La Frasnée',
    #                matched_name='Фране', country='France', score=0.9090909090909091)]

    find_city_in_string("Bavarian Environment Agency, Hans Högn Straße 12, "
                        "95030 Hof Saale, Bavaria, Germany", {"Germany"})
    # [LocationMatch(substring_range=(56, 59), substring='Hof', canonical_name='Hof',
    #                matched_name='Hof', country='Germany', score=1.0),
    #  LocationMatch(substring_range=(60, 65), substring='Saale', canonical_name='Saal',
    #                matched_name='Saal', country='Germany', score=0.8888888888888888),
    #  LocationMatch(substring_range=(39, 45), substring='Straße', canonical_name='Trassem',
    #                matched_name='Trassem', country='Germany', score=0.8571428571428571)]

    """
    Regions
    """

    find_region_in_string("Fur Museum, 7884 Fur, Denmark.", {"Denmark"})
    # [LocationMatch(substring_range=(0, 3), substring='Fur', canonical_name='Fur',
    #                matched_name='Fur', country='Denmark', score=1.0),
    #  LocationMatch(substring_range=(17, 20), substring='Fur', canonical_name='Fur',
    #                matched_name='Fur', country='Denmark', score=1.0),
    #  LocationMatch(substring_range=(22, 29), substring='Denmark',
    #                canonical_name='Kingdom of Denmark', matched_name='Denmark',
    #                country='Denmark', score=1.0)]

    find_region_in_string("Department of Biological Oceanography, Royal Netherlands Institute "
                          "for Sea Research (NIOZ), Texel, The Netherlands", {"Netherlands"})
    # [LocationMatch(substring_range=(45, 56), substring='Netherlands',
    #                canonical_name='Kingdom of the Netherlands', matched_name='Netherlands',
    #                country='Netherlands', score=1.0),
    #  LocationMatch(substring_range=(92, 97), substring='Texel', canonical_name='Texel',
    #                matched_name='Texel', country='Netherlands', score=1.0),
    #  LocationMatch(substring_range=(103, 114), substring='Netherlands',
    #                canonical_name='Kingdom of the Netherlands', matched_name='Netherlands',
    #                country='Netherlands', score=1.0)]


.. note::

    Whenever a country is considered part of another country ``normalize_country`` will return the latter.
    E.g., ``Puerto Rico`` is mapped to ``United States`` and ``Greenland`` to ``Denmark``.


Resource loading
~~~~~~~~~~~~~~~~

Resources for cities and regions aren't all loaded when you import ``TextScrubber``, they're loaded on the fly per
country. This means that the first time you do a query it can take a while. The second time around the same query will
be much faster, as will all other queries involving the same countr(y)(ies). You can load in resources per country in
advance by using:

.. code-block:: python

    from text_scrubber.geo import (add_city_resources, add_region_resources,
                                   normalize_country_to_country_codes)

    country_codes = normalize_country_to_country_codes(['Netherlands', 'China', 'USA'])
    add_city_resources(country_codes)
    add_region_resources(country_codes, progress_bar=True)

.. note::

    Whenever a country is considered part of another country ``normalize_country_to_country_codes`` returns both.

Cleaning
~~~~~~~~

There are clean functions available for countries/regions/cities, which all follow the same cleaning pipeline:

.. code-block:: python

    from text_scrubber.geo import clean_country, clean_region, clean_city

    clean_country('cent afr rep.')     # 'central african republic'
    clean_region('Hyōgo')              # 'hyogo'
    clean_city('płońsk')               # 'plonsk'
    clean_city('neustadt/westerwald')  # 'neustadt westerwald'


Documentation
-------------

If you want to build the documentation, please install the documentation dependencies by executing:

.. code-block:: bash

    pip install .[docs]

Documentation can be build by executing:

.. code-block:: bash

    python setup.py build_docs

Documentation can also be build from the ``docs`` folder directly. In that case ``text-scrubber`` should be installed
and available in your current working environment. Execute:

.. code-block:: bash

    make html

in the ``docs`` folder.
