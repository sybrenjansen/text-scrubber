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

which can then be used as

.. code-block:: python

    ts.transform('héLlô there, WòrlD')  # outputs 'hello world'

or

.. code-block:: python

    ts.transform(['héLlô there, WòrlD', 'slímm̀er ÀI'])  # outputs ['hello world', 'slimmer AI']


Geo
---

The ``geo`` module contains functions to normalize geographical data which deal with spelling errors, country name
variations, etc.:

.. code-block:: python

    from text_scrubber.geo import normalize_country, normalize_state, normalize_city

    # Countries
    normalize_country('Peoples rep. of China')  # ['China']
    normalize_country('Deutschland')            # ['Germany']
    normalize_country('st Nevis and Kitties')   # ['Saint Kitts and Nevis']
    normalize_country('ira')                    # ['Iran', 'Iraq']

    # States
    normalize_state('Qld')         # [('Queensland', 'Australia')]
    normalize_state('AR')          # [('Arkansas', 'United States'), ('Arunachal Pradesh', 'India')]
    normalize_state('King Kong')   # [('Hong Kong', 'China')]

    # Cities
    normalize_city('Leibnitz')    # [('Leibnitz', 'Austria')]
    normalize_city('heidelberg')  # [('Heidelberg', 'Australia'), ('Heidelberg', 'Germany'),
                                  #  ('Heidelberg', 'South Africa'), ('Heidelberg', 'United States')]
    normalize_city('texas')       # [('Texas City', 'United States')]
    normalize_city('Pari')        # [('Parai', 'Brazil'), ('Paris', 'Canada'), ('Paris', 'France'),
                                  #  ('Paris', 'United States'), ('Parit', 'Malaysia'),
                                  #  ('Pariz', 'Czech Republic')]


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
