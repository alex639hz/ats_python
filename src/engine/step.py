import sys
from time import time
from typing import TYPE_CHECKING, Callable

from engine.constants import *
from engine.types import LogInterface
from engine.utils import *

if TYPE_CHECKING:
    from engine.procedure import Procedure


class Step:
    def __init__(self, op, args, label, step_function):
        self.label = label
        self.op: STEP = op
        self.args = args
        self.func: Callable[..., str] = step_function

    def execute(self, procedure: Procedure):
        log = self.func(procedure)
        if log is not None:
            self.log(procedure, log)

        return

    def build_log(self, procedure, log):
        pass

    def log(self, procedure, log: str | LogInterface):
        if log == None:
            return

        if isinstance(log, str):
            msg = log
            args = None
        elif isinstance(log, dict):
            msg = log["msg"]
            args = log["args"]
        else:
            raise Exception()

        params = {
            "params": {
                "proc": procedure.label,
                "op": self.op.value,
                "step": self.label,
                "msg": msg,
            }
        }

        if args:
            params["params"]["args"] = args

        procedure.logger.info("-", extra=params)
        return

    def get_arg(self, key):
        return self.args.get(key)

    def get_args(self) -> dict:
        return self.args

    def get_op(self):
        return self.op
