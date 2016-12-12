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

from . import color
from . import metadata
from . import debouncer


FILENAME_REPLACEMENT = '%'


class PlainFormatter(logging.Formatter):
    STYLE = metadata.Map()
    LEVELS = metadata.Map()
    def format(self, record):
        msg = record.msg.format_map(self.STYLE)
        level = '{{{name}}}{name}{{/{name}}}'.format(
            name=record.levelname.lower()
        ).format_map(self.LEVELS)
        return '[ {} ]: {}'.format(level, msg % record.args)


class TTYFormatter(PlainFormatter):
    LEVELS = metadata.Map({
        'debug': (color.hex_to_ansi('477187'), color.reset()),
        'info': (color.hex_to_ansi('52a55d'), color.reset()),
        'warning': (color.hex_to_ansi('d4a46a'), color.reset()),
        'error': (color.hex_to_ansi('d4706a'), color.reset()),
    })
    STYLE = metadata.Map({
        'path': (color.hex_to_ansi('ffd8aa'), color.reset()),
        'cmd': ('`' + color.hex_to_ansi('6f90a2'), color.reset() + '`'),
        'num': (color.hex_to_ansi('84c68c'), color.reset())
    })


class EventHandler(FileSystemEventHandler):
    def __init__(self, filter, command):
        self.filter = filter
        self.command = command

    def on_any_event(self, e):
        if self.filter(e):
            logging.getLogger(__name__).info(
                '{path}%s{/path} %s', e.src_path, e.event_type)
            self.command(e)
        else:
            logging.getLogger(__name__).debug(
                '{path}%s{/path} %s ignored', e.src_path, e.event_type)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('path', help='the path to watch (recursive)')
    command_help = (
        'remaining positional arguments are the command to execute. '
        'use {!r} to substitute the filename of the change event'
    )
    p.add_argument('command',
        nargs=argparse.REMAINDER,
        help=command_help.format(FILENAME_REPLACEMENT).replace('%', '%%'))
    p.add_argument('-i', '--include',
        action='append', metavar='PATTERN',
        help='glob pattern to include. can be specified more than once')
    p.add_argument('-x', '--exclude',
        action='append', metavar='PATTERN',
        help='glob pattern to exclude. can be specified more than once')
    p.add_argument('-l', '--latency',
        type=float, default=1.0, metavar='SECONDS',
        help='latency (in seconds) between runs')
    p.add_argument('-q', '--quiet',
        action='store_true',
        help='set verbosity to a minimum')
    p.add_argument('--debug',
        action='store_true',
        help='set verbosity very high')
    p.add_argument('-L', '--log-file',
        metavar='PATH',
        help='specify a file to append logs to')
    p.add_argument('-C', '--no-color', action='store_true')
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
        cmd = [x.replace(FILENAME_REPLACEMENT, e.src_path) for x in args]
        logging.getLogger(__name__).info(
            'running {cmd}%s{/cmd}', ' '.join(map(shlex.quote, cmd)))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as error:
            logging.getLogger(__name__).error(
                '{cmd}%s{/cmd} returned {num}%d{/num}',
                ' '.join(map(shlex.quote, cmd)), error.returncode)
        else:
            logging.getLogger(__name__).debug(
                '{cmd}%s{/cmd} returned {num}0{/num}',
                ' '.join(map(shlex.quote, cmd)))

    return inner


def setup_logging(opts):
    logger = logging.getLogger(__name__)
    if opts.debug:
        logger.setLevel(logging.DEBUG)
    elif opts.quiet:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

    if opts.log_file:
        handler = logging.FileHandler(opts.log_file)
    else:
        handler = logging.StreamHandler()

    if sys.stdin.isatty() and not opts.no_color and not opts.log_file:
        handler.setFormatter(TTYFormatter())
    else:
        handler.setFormatter(PlainFormatter())

    logger.addHandler(handler)


def main():
    opts = parse_args()
    setup_logging(opts)
    callback = debouncer.Debouncer(get_command(opts.command), resolution=opts.latency)
    handler = EventHandler(
        get_filter(opts.include, opts.exclude),
        callback
    )
    observer = Observer()
    observer.schedule(handler, opts.path, recursive=True)
    callback.start()
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        callback.stop()
    observer.join()
    callback.join()


if __name__ == '__main__':
    main()
