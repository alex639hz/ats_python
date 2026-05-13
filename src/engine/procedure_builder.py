import sys
from time import time
from typing import TYPE_CHECKING

from engine.constants import *
from engine.utils import *
from engine.step import Step
from engine.step_functions import step_functions

from engine.procedure import Procedure

# if TYPE_CHECKING:


class ProcedureBuilder:

    def __init__(self, label):
        self.label: str = label
        self.steps: list["Step"] = []

    def append_step(self, op: DEF_STEP, args, label):
        step = Step(op, args, label, step_functions[op])
        self.steps.append(step)
        return self

    def generate_procedure(self) -> Procedure:
        procedure = Procedure(self.label)

        for step in self.steps:
            procedure.step_append(step)

        procedure.start()

        return procedure

    def add_fnull(self, lable):
        self.append_step(DEF_STEP.NULL, NOARG, lable)

    def add_fexit(self, lable="exit"):
        self.append_step(DEF_STEP.EXIT, NOARG, lable)

    def add_fcall(self, fcall, fargs, lable):
        step_args = {
            DEF_STEP_ARG.FUNC_CALL: fcall,
            DEF_STEP_ARG.FUNC_ARGS: fargs,
        }
        self.append_step(
            DEF_STEP.FCALL,
            step_args,
            lable,
        )

    def add_fwait(self, seconds: float, lable=DEF_NO_LABEL):
        args = {DEF_STEP_ARG.DURATION_SECONDS: seconds}
        self.append_step(DEF_STEP.TIMER_START, args, lable)
        self.append_step(DEF_STEP.TIMER_WAIT, args, DEF_NO_LABEL)

    def add_worker(self, fcall, fargs, thread_name: str, lable=""):
        step_args = {
            DEF_STEP_ARG.FUNC_CALL: fcall,
            DEF_STEP_ARG.FUNC_ARGS: fargs,
            DEF_STEP_ARG.TITLE: thread_name,
        }
        self.append_step(DEF_STEP.WORKER_START, step_args, lable)

    def add_worker_check(self, thread_name, lable=None):
        step_args = {
            DEF_STEP_ARG.TITLE: thread_name,
        }
        self.append_step(
            DEF_STEP.WORKER_WAIT,
            step_args,
            lable,
        )
