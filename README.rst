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
country name variations, etc.:

.. code-block:: python

    from text_scrubber.geo import normalize_country, normalize_region, normalize_city

    """
    Countries
    """

    normalize_country('Peoples rep. of China')
    # [Location(canonical_name='China', matched_name='Peoples Republic of China', country=None,
    #           score=1.0)]

    normalize_country('Deutschland')
    # [Location(canonical_name='Germany', matched_name='Deutschland', country=None, score=1.0)]

    normalize_country('st Nevis and Kitties')
    # [Location(canonical_name='Saint Kitts and Nevis', matched_name='Saint Kitts and Nevis',
    #           country=None, score=0.75)]

    normalize_country('ira')
    # [Location(canonical_name='Iran', matched_name='Iran', country=None, score=0.857...),
    #  Location(canonical_name='Iraq', matched_name='Iraq', country=None, score=0.857...)]

    """
    Cities
    """

    normalize_city('Leibnitz', ['Austria'])
    # [Location(canonical_name='Leibnitz', matched_name='Leibnitz', country='Austria', score=1.0)]

    normalize_city('heidelberg')
    # [Location(canonical_name='Heidelberg', matched_name='Heidelberg', country='Germany',
    #           score=1.0),
    #  Location(canonical_name='Heidelberg', matched_name='Heidelberg', country='South Africa',
    #           score=1.0),
    #  Location(canonical_name='Heidelberg', matched_name='Heidelberg', country='United States',
    #           score=1.0)]

    normalize_city('ohioo', ['US'])
    # [Location(canonical_name='Ohio', matched_name='Ohio', country='United States',
    #           score=0.888...)]

    normalize_city('Madri', ['Spain', 'US', 'Brazil'])
    # [Location(canonical_name='Madrid', matched_name='Madrid', country='Spain',
    #           score=0.909...),
    #  Location(canonical_name='Madrid', matched_name='Madrid', country='United States',
    #           score=0.909...),
    #  Location(canonical_name='Mari', matched_name='Mari', country='Brazil',
    #           score=0.888...)]

    """
    Regions
    """

    normalize_region('triangle park', ['US'])
    # [Location(canonical_name='The Triangle Park', matched_name='The Triangle Park',
    #           country='United States', score=1.0)]

    normalize_region('Fur', ['Denmark'])
    # [Location(canonical_name='Fur', matched_name='Fur', country='Denmark', score=1.0)]

    normalize_region('texel', ['NL'])
    # [Location(canonical_name='Texel', matched_name='Texel', country='Netherlands', score=1.0)]


Each of the above normalization functions return the canonical name, matched name, the match score, and when normalizing
cities or regions it will also contain the corresponding country. The difference between canonical and matched name
stems from the fact that some countries, cities, or regions can have alternative names. E.g., ``NYC`` maps to
``New York City``. When the query was ``NYCC`` the canonical name will be ``New York City``, but the matched name
``NYC``. The match scores are always between 0.0 and 1.0, where 1.0 is a perfect match. If a known mapping exists, like
``Deutschland`` to ``Germany``, then the match score will be 1.0.

.. note::

    When normalizing a country or finding countries in a string, the ``country`` attribute of a ``LocationMatch`` object
    is always ``None``. The normalized name can be found using the ``canonical_name`` attribute.

The ``text_scrubber.geo`` module also contains functions to find the name of places (country, region, and city) in
text dealing with spelling errors, country name variations, etc.:

.. code-block:: python

    from text_scrubber.geo import (find_city_in_string, find_country_in_string,
                                   find_region_in_string)

    """
    Countries
    """

    find_country_in_string("Institute of German study, Accra, Ghana")
    # [ExtractedLocation(location=Location(canonical_name='Ghana', matched_name='Ghana',
    #                                      country=None, score=1.0),
    #                    substring='Ghana', substring_range=Range(start=34, end=39)),
    #  ExtractedLocation(location=Location(canonical_name='Germany', matched_name='Germany',
    #                                      country=None, score=0.923...),
    #                    substring='German', substring_range=Range(start=13, end=19))]

    find_country_in_string("Peking University, 5 Yiheyuan Rd, "
                           "Haidian District, Beijing, CH, 100871")
    # This was a trick question though, as CH=Switzerland. China is CN
    # [ExtractedLocation(location=Location(canonical_name='Switzerland', matched_name='CH',
    #                                      country=None, score=1.0),
    #                    substring='CH', substring_range=Range(start=61, end=63))]

    """
    Cities
    """

    find_city_in_string("Météorage Pau France", {"France"})
    # [ExtractedLocation(location=Location(canonical_name='Pau', matched_name='Pau',
    #                                      country='France', score=1.0),
    #                    substring='Pau', substring_range=Range(start=10, end=13)),
    #  ExtractedLocation(location=Location(canonical_name='La Frasnée', matched_name='Фране',
    #                                      country='France', score=0.909...),
    #                    substring='France', substring_range=Range(start=14, end=20))]

    find_city_in_string("Bavarian Environment Agency, Hans Högn Straße 12, "
                        "95030 Hof Saale, Bavaria, Germany", {"Germany"})
    # [ExtractedLocation(location=Location(canonical_name='Hof', matched_name='Hof',
    #                                      country='Germany', score=1.0),
    #                    substring='Hof', substring_range=Range(start=56, end=59)),
    #  ExtractedLocation(location=Location(canonical_name='Saal', matched_name='Saal',
    #                                      country='Germany', score=0.888...),
    #                    substring='Saale', substring_range=Range(start=60, end=65)),
    #  ExtractedLocation(location=Location(canonical_name='Trassem', matched_name='Trassem',
    #                                      country='Germany', score=0.857...),
    #                    substring='Straße', substring_range=Range(start=39, end=45))]

    """
    Regions
    """

    find_region_in_string("Fur Museum, 7884 Fur, Denmark.", {"Denmark"})
    # [ExtractedLocation(location=Location(canonical_name='Fur', matched_name='Fur',
    #                                      country='Denmark', score=1.0),
    #                    substring='Fur', substring_range=Range(start=0, end=3)),
    #  ExtractedLocation(location=Location(canonical_name='Fur', matched_name='Fur',
    #                                      country='Denmark', score=1.0),
    #                    substring='Fur', substring_range=Range(start=17, end=20)),
    #  ExtractedLocation(location=Location(canonical_name='Kingdom of Denmark',
    #                                      matched_name='Denmark', country='Denmark', score=1.0),
    #                    substring='Denmark', substring_range=Range(start=22, end=29))]

    find_region_in_string("Department of Biological Oceanography, Royal Netherlands Institute "
                          "for Sea Research (NIOZ), Texel, The Netherlands", {"Netherlands"})
    # [ExtractedLocation(location=Location(canonical_name='Kingdom of the Netherlands',
    #                                      matched_name='Netherlands', country='Netherlands',
    #                                      score=1.0),
    #                    substring='Netherlands', substring_range=Range(start=45, end=56)),
    #  ExtractedLocation(location=Location(canonical_name='Texel', matched_name='Texel',
    #                                      country='Netherlands', score=1.0),
    #                    substring='Texel', substring_range=Range(start=92, end=97)),
    #  ExtractedLocation(location=Location(canonical_name='Kingdom of the Netherlands',
    #                                      matched_name='Netherlands', country='Netherlands',
    #                                      score=1.0),
    #                    substring='Netherlands', substring_range=Range(start=103, end=114))]

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
