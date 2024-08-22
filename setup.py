from setuptools import setup, find_packages

# Read long description from README.rst
with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='text-scrubber',
    version='0.4.2',
    author='Sybren Jansen',
    description='Python package that offers text scrubbing functionality, providing building blocks for string '
                'cleaning as well as normalizing geographical text (countries/states/cities)',
    long_description=long_description,
    url='https://github.com/sybrenjansen/text-scrubber',
    license='MIT',
    packages=find_packages(),
    install_requires=['anyascii',
                      'cython',
                      'ftfy',
                      'num2words',
                      'numpy',
                      'pylatexenc',
                      'python-Levenshtein',
                      'scipy',
                      'tqdm'],
    include_package_data=True,
    extras_require={'docs': ['sphinx>=5,<6',
                             'sphinx-rtd-theme==0.5.0',
                             'sphinx-autodoc-typehints==1.11.0',
                             'sphinx-versions==1.1.3',
                             'click==8.0.4'],
                    'tests': ['nose2', 'numpy']},
    test_suite='nose2.collector.collector',
    tests_require=['nose2', 'numpy'],
    classifiers=[
        # Development status
        'Development Status :: 5 - Production/Stable',

        # Supported Python versions
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',

        # License
        'License :: OSI Approved :: MIT License',

        # Topic
        'Topic :: Text Processing'
    ]
)
