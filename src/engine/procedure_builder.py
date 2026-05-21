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

    def append_step(self, op: STEP, args, label):
        step = Step(op, args, label, step_functions[op])
        self.steps.append(step)
        return self

    def generate_procedure(self) -> Procedure:
        procedure = Procedure(self.label)

        for step in self.steps:
            procedure.step_append(step)

        procedure.start()

        return procedure

    def add_step_null(self, label):
        self.append_step(STEP.NULL, NOARG, label)

    def add_step_exit(self, label="exit"):
        self.append_step(STEP.EXIT, NOARG, label)

    def add_step_function(self, function, args, label):
        step_args = {
            STEP_ARG.FUNCTION: function,
            STEP_ARG.ARGS: args,
        }
        self.append_step(
            STEP.FUNCTION_CALL,
            step_args,
            label,
        )

    def add_step_delay(self, seconds: float, label=DEF_NO_LABEL):
        args = {STEP_ARG.DURATION_SECONDS: seconds}
        self.append_step(STEP.DELAY_START, args, label)
        self.append_step(STEP.DELAY_WAIT, args, DEF_NO_LABEL)

    def add_step_worker_start(self, thread_name: str, function, args, label=""):
        step_args = {
            STEP_ARG.FUNCTION: function,
            STEP_ARG.ARGS: args,
            STEP_ARG.TITLE: thread_name,
        }
        self.append_step(STEP.WORKER_START, step_args, label)

    def add_step_worker_wait(self, thread_name, label=None):
        step_args = {
            STEP_ARG.TITLE: thread_name,
        }
        self.append_step(
            STEP.WORKER_WAIT,
            step_args,
            label,
        )
