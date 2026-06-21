import threading
from typing import TYPE_CHECKING, Callable

from project.types import StepInterface
from engine.utils import Utils

if TYPE_CHECKING:
    from engine.procedure import Procedure


class Worker:
    def __init__(self, procedure: Procedure, func: Callable, args={}, thread_name=""):
        self.name = thread_name
        worker_tuple = (procedure, args)
        worker_interface: StepInterface = {
            "procedure": procedure,
            "args": args,
        }
        self.thread = Utils.thread_define(thread_name, func, worker_interface)
        self.thread_complete = threading.Event()

    def start(self):
        self.thread.start()

    def is_complete(self):
        return self.thread_complete.is_set()

    def set_complete(self):
        self.thread_complete.set()

    def wait(self):
        return self.thread.join()
