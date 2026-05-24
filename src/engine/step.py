import sys
from time import time
from typing import TYPE_CHECKING

from engine.constants import *
from engine.utils import *

if TYPE_CHECKING:
    from engine.procedure import Procedure


class Step:
    def __init__(self, op, args, label, step_function):
        self.label = label or "NA"
        self.op: STEP = op
        self.args = args
        self.func = step_function
        self.logger = logging.getLogger("[STEP]")

    def execute(self, procedure: Procedure):
        log_msg = self.func(procedure)
        if log_msg:
            self.log(procedure, log_msg)

        return

    def log(self, procedure: Procedure, msg=""):
        proc_label = procedure.get_label()
        log_msg = f"{proc_label}: {self.op.value}\t{self.label}\t{msg}"
        self.logger.info(log_msg)
        return

    def get_arg(self, key):
        return self.args.get(key)

    def get_args(self) -> dict:
        return self.args

    def get_label(self):
        return self.label

    def get_op(self):
        return self.op
