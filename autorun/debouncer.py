import time
import threading
from collections import namedtuple


Event = namedtuple('Event', 'args kwargs')


class Debouncer(threading.Thread):
    def __init__(self, fn, resolution=1):
        super().__init__()
        self._fn = fn
        self._arg = None
        self._resolution = resolution
        self._mux = threading.Lock()
        self._event = threading.Event()
        self._stop_event = threading.Event()

    def __call__(self, *args, **kwargs):
        self._push(Event(args=args, kwargs=kwargs))

    def _push(self, event):
        with self._mux:
            self._arg = event
            self._event.set()

    def stop(self):
        self._stop_event.set()
        self._event.set()  # just in case we are blocking here

    def run(self):
        while True:
            if not self._event.wait(self._resolution):
                continue

            # got an event, now check if we need to stop
            # and also block until everything settles down
            if self._stop_event.wait(self._resolution):
                return

            # we've waited long enough, extract the arg and clear the event
            with self._mux:
                arg = self._arg
                self._event.clear()

            # run the command
            self._fn(*arg.args, **arg.kwargs)
