import threading
from typing import Callable

from engine.procedure import Procedure
from engine.utils import Utils


class Worker:
    def __init__(self, procedure: Procedure, func: Callable, args={}, thread_name=""):
        self.thread = Utils.thread_define(thread_name, func, (procedure, args))
        self.complete = threading.Event()

    def start(self):
        self.thread.start()

    def is_complete(self):
        return self.complete.is_set()

    def wait(self):
        return self.thread.join()
