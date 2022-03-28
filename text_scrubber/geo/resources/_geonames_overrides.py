# Add some manual alternate names and parent-child hierarchy. The hierarchy is {parent: list of children names}.
# Note that many hierarchy things are already fixed by using the hierarchy file of geonames, but not everything is.
MANUAL_ALTERNATE_NAMES = {
    'JP': {'Gifu-shi': ['Gifu']}
}
MANUAL_HIERARCHY = {
    'GB': {'Newcastle upon Tyne': ['Newcastle']},
    'IN': {'New Delhi': ['Delhi']},
    'IT': {'Genoa': ['Genova'],
           'Milan': ['Milano']},
    'US': {'New York City': ['Manhatten', 'New York', 'Queens']}
}
