import threading
from typing import TYPE_CHECKING, Callable

from engine.utils import Utils

if TYPE_CHECKING:
    from engine.procedure import Procedure


class Worker:
    def __init__(self, procedure: Procedure, func: Callable, args={}, thread_name=""):
        self.name = thread_name
        self.thread = Utils.thread_define(thread_name, func, (procedure, args))
        self.thread_complete = threading.Event()

    def start(self):
        self.thread.start()

    def is_complete(self):
        return self.thread_complete.is_set()

    def set_complete(self):
        self.thread_complete.set()

    def wait(self):
        return self.thread.join()
