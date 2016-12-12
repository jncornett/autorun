#!/usr/bin/env python3

import argparse
import logging
import fnmatch
import time
import subprocess
import sys
import shlex

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Map(dict):
    def __missing__(self, key):
        return ''


def format_ansi(mappings, string):
    return string.format_map(Map(mappings))


def isatty():
    return sys.stderr.isatty()


class PlainFormatter(logging.Formatter):
    STYLE = {}
    def format(self, record):
        msg = format_ansi(self.STYLE, record.msg)
        level = record.levelname.lower()
        level_fmt = '{%s}%s{/}' % (level, level)
        level_out = format_ansi(self.STYLE, level_fmt)
        return '[ %s ]: %s' % (level_out, msg % record.args)


class TTYFormatter(PlainFormatter):
    STYLE = {
        'debug': '\x1b[34m',
        'info': '\x1b[32m',
        'warning': '\x1b[33m',
        'error': '\x1b[31m',
        'path': '\x1b[35m',
        'cmd': '\x1b[36m',
        '/': '\x1b[0m'
    }


class EventHandler(FileSystemEventHandler):
    def __init__(self, filter, command):
        self.filter = filter
        self.command = command

    def on_any_event(self, e):
        if self.filter(e):
            logging.getLogger(__name__).info(
                '{path}%s{/} %s', e.src_path, e.event_type)
            self.command(e)
        else:
            logging.getLogger(__name__).debug(
                '{path}%s{/} %s ignored', e.src_path, e.event_type)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('path', help='the path to watch (recursive)')
    p.add_argument('command',
        nargs=argparse.REMAINDER,
        help='remaining positional arguments as the command to execute')
    p.add_argument('-i', '--include',
        action='append', metavar='PATTERN',
        help='glob pattern to include. can be specified more than once')
    p.add_argument('-x', '--exclude',
        action='append', metavar='PATTERN',
        help='glob pattern to exclude. can be specified more than once')
    p.add_argument('-q', '--quiet',
        action='store_true',
        help='set verbosity to a minimum')
    p.add_argument('--debug',
        action='store_true',
        help='set verbosity very high')
    opts = p.parse_args()
    return opts


def make_glob_filter(includes, excludes):
    def inner(string):
        if includes:
            if not any(fnmatch.fnmatch(string, i) for i in includes):
                return False

        if any(fnmatch.fnmatch(string, x) for x in excludes):
            return False

        return True

    return inner


def get_filter(includes, excludes):
    glob_filter = make_glob_filter(includes or [], excludes or[])
    def inner(e):
        if e.is_directory:
            return False

        if e.event_type not in ('modified', 'created', 'deleted', 'moved'):
            return False

        return glob_filter(e.src_path)

    return inner


def get_command(args):
    def inner(e):
        cmd = [x.replace('%', e.src_path) for x in args]
        logging.getLogger(__name__).info(
            'running {cmd}%s{/}', ' '.join(map(shlex.quote, cmd)))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as error:
            logging.getLogger(__name__).error(
                'returned %d', error.returncode)

    return inner


def setup_logging(logger, tty, debug, quiet):
    if debug:
        logger.setLevel(logging.DEBUG)
    elif quiet:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    if tty:
        handler.setFormatter(TTYFormatter())
    else:
        handler.setFormatter(PlainFormatter())

    logger.addHandler(handler)


def main():
    opts = parse_args()
    setup_logging(logging.getLogger(__name__), isatty(), opts.debug, opts.quiet)
    handler = EventHandler(
        get_filter(opts.include, opts.exclude),
        get_command(opts.command)
    )
    observer = Observer()
    observer.schedule(handler, opts.path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
