import re


def hex_to_ansi(hex, foreground=True):
    """
    >>> hex_to_ansi('fff')
    '\\x1b[38;2;255;255;255m'
    >>> hex_to_ansi('#fff')
    '\\x1b[38;2;255;255;255m'
    >>> hex_to_ansi('010101')
    '\\x1b[38;2;1;1;1m'
    >>> hex_to_ansi('#010101')
    '\\x1b[38;2;1;1;1m'
    >>> hex_to_ansi('#010101', foreground=False)
    '\\x1b[48;2;1;1;1m'
    >>> hex_to_ansi('#')
    ''
    >>> hex_to_ansi('')
    ''
    """
    m = re.match(r'#?([a-f0-9]{2})([a-f0-9]{2})([a-f0-9]{2})', hex)
    m = m or re.match(r'#?([a-f0-9])([a-f0-9])([a-f0-9])', hex)
    if not m:
        return ''

    r, g, b = (int(x if len(x) == 2 else x + 'f', 16) for x in m.groups())
    return '\x1b[{};2;{};{};{}m'.format(38 if foreground else 48, r, g, b)


def reset():
    return '\x1b[0m'
