class Map(dict):
    """
    >>> m = Map()
    >>> m
    {}
    >>> m['key'] = ('left', 'right')
    >>> m['key']
    'left'
    >>> m['/key']
    'right'
    >>> m['missing']
    ''
    >>> m['/missing']
    ''
    >>> m[''] = '[]'
    >>> m['']
    '['
    >>> m['/']
    ']'
    """
    def __getitem__(self, key):
        close = key.startswith('/')
        if close:
            key = key[1:]

        value = super().__getitem__(key)
        return value[close] if value else value

    def __missing__(self, key):
        return ''
