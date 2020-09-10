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

    from text_scrubber.geo import normalize_country, normalize_state, normalize_city

    # Countries
    normalize_country('Peoples rep. of China')  # ['China']
    normalize_country('Deutschland')            # ['Germany']
    normalize_country('st Nevis and Kitties')   # ['Saint Kitts and Nevis']
    normalize_country('ira')                    # ['Iran', 'Iraq']

    # States
    normalize_state('Qld')         # [('Queensland', 'Australia')]
    normalize_state('AR')          # [('Arkansas', 'United States'),
                                   #  ('Arunachal Pradesh', 'India')]
    normalize_state('King Kong')   # [('Hong Kong', 'China')]

    # Cities
    normalize_city('Leibnitz')    # [('Leibnitz', 'Austria')]
    normalize_city('heidelberg')  # [('Heidelberg', 'Australia'), ('Heidelberg', 'Germany'),
                                  #  ('Heidelberg', 'South Africa'),
                                  #  ('Heidelberg', 'United States')]
    normalize_city('texas')       # [('Texas City', 'United States')]
    normalize_city('Pari')        # [('Parai', 'Brazil'), ('Paris', 'Canada'),
                                  #  ('Paris', 'France'), ('Paris', 'United States'),
                                  #  ('Parit', 'Malaysia'), ('Pariz', 'Czech Republic')]

.. warning::

    There's a good chance that the list of states/cities is not complete for all countries.

.. note::

    Whenever a country is considered part of another country ``normalize_country`` will return the latter.
    E.g., ``Puerto Rico`` is mapped to ``United States`` and ``Greenland`` to ``Denmark``.


Cleaning
~~~~~~~~

There are clean functions available for countries/states/cities, which all follow the same cleaning pipeline:

.. code-block:: python

    from text_scrubber.geo import clean_country, clean_state, clean_city

    clean_country('cent afr rep.')     # 'central african republic'
    clean_state('Hyōgo')               # 'hyogo'
    clean_city('płońsk')               # 'plonsk'
    clean_city('neustadt/westerwald')  # 'neustadt westerwald'
