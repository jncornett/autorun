#!/usr/bin/env python3

import argparse
import logging
import fnmatch
import time
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def __init__(self, filter, command):
        self.filter = filter
        self.command = command

    def on_any_event(self, e):
        if self.filter(e):
            self.command(e)
        else:
            logging.debug("ignoring %s on %r", e.event_type, e.src_path)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.add_argument("-i", "--include", action='append')
    p.add_argument("-x", "--exclude", action='append')
    p.add_argument("--debug", action='store_true')
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
        logging.info("%r changed", e.src_path)
        cmd = [x.format(e.src_path) for x in args]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            logging.error("%s: %s", cmd, e)

    return inner


def main():
    opts = parse_args()
    logging.basicConfig(level=logging.DEBUG if opts.debug else logging.INFO)
    handler = MyHandler(
        get_filter(opts.include, opts.exclude),
        get_command(opts.command)
    )
    observer = Observer()
    observer.schedule(handler, opts.path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
