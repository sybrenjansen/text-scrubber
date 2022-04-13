Basic usage
===========

.. contents:: Contents
    :depth: 2
    :local:

TextScrubber
------------

The :obj:`text_scrubber.text_scrubber.TextScrubber` class cleans a single or a collection of strings. It can be easily
constructed and configured with building blocks:

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

For a complete list of building blocks please refer to the :obj:`text_scrubber.text_scrubber.TextScrubber` API
reference.


Geo
---

The :obj:`text_scrubber.geo` module contains functions to normalize geographical data which deal with spelling errors,
country name variations, etc.:

.. code-block:: python

    from text_scrubber.geo import normalize_country, normalize_region, normalize_city

    # Countries
    normalize_country('Peoples rep. of China')  # [('China', 1.0)]
    normalize_country('Deutschland')            # [('Germany', 1.0)]
    normalize_country('st Nevis and Kitties')   # [('Saint Kitts and Nevis', 0.75)]
    normalize_country('ira')                    # [('Iran', 0.857), ('Iraq', 0.857)]

    # Cities
    normalize_city('Leibnitz', ['Austria'])    # [('Leibnitz', 'Austria', 1.0)]
    normalize_city('heidelberg')  # [('Heidelberg', 'Germany', 1.0), 
                                  #  ('Heidelberg', 'South Africa', 1.0),
                                  #  ('Heidelberg', 'United States', 1.0)]
    normalize_city('ohioo', ['US'])  # [('Ohio', 'United States', 0.889)]
    normalize_city('Madri', ['Spain', 'US', 'Brazil'])  # [('Madrid', 'Spain', 0.909),
                                                        #  ('Madrid', 'United States', 0.909),
                                                        #  ('Mari', 'Brazil', 0.889)]

    # Regions
    normalize_region('triangle park', ['US'])   # [('The Triangle Park', 'United States', 1.0)]
    normalize_region('Fur', ['Denmark'])        # [('Fur', 'Denmark', 1.0)]
    normalize_region('texel', ['NL'])            # [('Texel', 'Netherlands', 1.0)]

Each of the above normalization functions will return the match score as last entry in the tuple. These scores are
always between 0.0 and 1.0, where 1.0 is a perfect match. If a known mapping exists, like ``Deutschland`` to
``Germany``, then the match score will be 1.0.

The :obj:`text_scrubber.geo` module also contains functions to find the name of places (country, region, and city) in
text dealing with spelling errors, country name variations, etc.:

.. code-block:: python

    from text_scrubber.geo import (find_city_in_string, find_country_in_string,
                                   find_region_in_string)

    # Countries
    find_country_in_string("Institute of German study, Accra, Ghana")
    # Returns: [Match(substring_range=(34, 39), substring='Ghana',
    #                 normalized='Ghana', score=1.0),
    #           Match(substring_range=(13, 19), substring='German',
    #                 normalized='Germany', score=0.923)]

    find_country_in_string("Peking University, 5 Yiheyuan Rd, "
                           "Haidian District, Beijing, CH, 100871")
    # Returns: [Match(substring_range=(61, 63), substring="CH",
    #                 normalized="China", score=1.0)]

    # Cities
    find_city_in_string("Météorage Pau France", {"France"})
    # Returns: [Match(substring_range=(10, 13), substring="Pau",
    #                 normalized=("Pau", "France"), score=1.0),
    #           Match(substring_range=(14, 20), substring="France",
    #                 normalized=("La Frasnée", "France"), score=0.909)]

    find_city_in_string("Bavarian Environment Agency, Hans Högn Straße 12, "
                        "95030 Hof Saale, Bavaria, Germany", {"Germany})
    # Returns: [Match(substring_range=(56, 59), substring='Hof',
    #                 normalized=('Hof', 'Germany'), score=1.0),
    #           Match(substring_range=(39, 45), substring="Straße",
    #                 normalized=("Trassem", "Germany"), score=0.857)]

    # Regions
    find_region_in_string("Fur Museum, 7884 Fur, Denmark.", {"Denmark"})
    # Returns: [Match(substring_range=(0, 3), substring='Fur',
    #                 normalized=('Fur', 'Denmark'), score=1.0),
    #           Match(substring_range=(17, 20), substring='Fur',
    #                 normalized=('Fur', 'Denmark'), score=1.0),
    #           Match(substring_range=(22, 29), substring='Denmark',
    #                 normalized=('Kingdom of Denmark', 'Denmark'), score=1.0)]

    find_region_in_string("Department of Biological Oceanography, Royal Netherlands Institute "
                          "for Sea Research (NIOZ), Texel, The Netherlands", {"Netherlands"})
    # Returns: [Match(substring_range=(45, 56), substring='Netherlands',
    #                 normalized=('Kingdom of the Netherlands', 'Netherlands'), score=1.0),
    #           Match(substring_range=(92, 97), substring='Texel',
    #                 normalized=('Texel', 'Netherlands'), score=1.0),
    #           Match(substring_range=(103, 114), substring='Netherlands',
    #                 normalized=('Kingdom of the Netherlands', 'Netherlands'), score=1.0)]

.. note::

    Whenever a country is considered part of another country ``normalize_country`` will return the latter.
    E.g., ``Puerto Rico`` is mapped to ``United States`` and ``Greenland`` to ``Denmark``.


Cleaning
~~~~~~~~

There are clean functions available for countries/regions/cities, which all follow the same cleaning pipeline:

.. code-block:: python

    from text_scrubber.geo import clean_country, clean_region, clean_city

    clean_country('cent afr rep.')     # 'central african republic'
    clean_region('Hyōgo')              # 'hyogo'
    clean_city('płońsk')               # 'plonsk'
    clean_city('neustadt/westerwald')  # 'neustadt westerwald'
