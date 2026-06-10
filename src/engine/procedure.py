from datetime import datetime
from time import time
from typing import TYPE_CHECKING
import logging


from engine.session import Session
from engine.constants import *
from engine.utils import *
from engine.step import Step
from engine.worker import Worker

from engine.db import Db, database

if TYPE_CHECKING:
    from engine.framework import Framework


class Procedure:

    def __init__(self, label):
        # private initialized by constructor
        self._label: str = label

        # private uninitialized by constructor
        self._steps: list["Step"] = []
        self._index = 0
        self._is_running = False
        self._is_first_run = True
        self._nextstate = self.nextstate_init()

        # public
        self.logger: logging.Logger  # = logging.getLogger("[procedure]")
        self.collection_name = "session"
        self.session = Session(self)
        self.framework: Framework
        self.db: Db

    def framework_set(self, framework: Framework):
        self.logger = framework.logger
        self.framework = framework
        self.db = framework.db
        return self

    def get_worker_from_active_step(self) -> Worker:
        """return worker reference from procedure session. This function valid ONLY for WORKER_START step"""
        step_args = self.get_active_step().get_args()
        worker_name = step_args.get(STEP_ARG.TITLE)  # [STEP_ARG.TITLE]
        if not worker_name:
            raise Exception(f"missing worker in active step")
        worker: Worker | None = self.session.attribute_get(worker_name)
        if not worker:
            raise Exception(f"missing worker in active step")
        return worker

    def execution_processor(self, framework: Framework):
        step = self.get_active_step()
        self.nextstate_next()  # Default
        res = step.func(self)
        try:
            pass
        except Exception as e:
            msg = f"step exception: {step.get_label() or step.func.__name__} {e}"
            self.nextstate_exit(msg)
            return

        if res:
            step.log(self, res)

        self._nextstate_processor()
        return

    def step_append(self, step: Step):
        self._steps.append(step)
        return self

    def get_active_step(self) -> Step:
        return self._steps[self._index]

    def get_label(self) -> str:
        return self._label

    def add_steps(self, new_steps: list[Step]):
        self._steps.extend(new_steps)
        return self

    def get_step_by_label(self, label: str):
        for step in self._steps:
            if step.get_label() == label:
                return step
        raise Exception(
            f"Step with label {label} not found in procedure {self.get_label()}"
        )

    def is_running(self):
        return self._is_running

    def start(self):
        self._is_running = True
        return self

    def stop(self):
        self._is_running = False
        return self

    def _nextstate_processor(self):

        final_index = len(self._steps) - 1
        nextstate_op = self._nextstate[0]
        payload = self._nextstate[1]
        is_index_range_ok = self._index < final_index

        if nextstate_op == DEF_NEXTSTATE_OP.NEXT and is_index_range_ok:
            self._increase_index()
        elif nextstate_op == DEF_NEXTSTATE_OP.NEXT and not is_index_range_ok:
            self.stop()
        elif nextstate_op == DEF_NEXTSTATE_OP.STAY:
            pass
        elif nextstate_op == DEF_NEXTSTATE_OP.PAUSE:
            self.stop()
        elif nextstate_op == DEF_NEXTSTATE_OP.JUMP:
            if not isinstance(payload, int):
                raise Exception(f"invalid payload for JUMP: {payload}")
            self._index = payload

        elif nextstate_op == DEF_NEXTSTATE_OP.ERROR:
            pass
        else:
            raise Exception(f"Undefined nextstate_op: {nextstate_op}")

        return self

    def nextstate_init(self):
        self._nextstate = (DEF_NEXTSTATE_OP.PAUSE, None)
        return self._nextstate

    def nextstate_set(self, nextstate_op: DEF_NEXTSTATE_OP, idx=0):
        self._nextstate = (nextstate_op, idx)

    def nextstate_next(self):
        self.nextstate_set(DEF_NEXTSTATE_OP.NEXT)

    def nextstate_stay(self):
        self.nextstate_set(DEF_NEXTSTATE_OP.STAY)

    def nextstate_jump_by_label(self, label: str):
        for index, step in enumerate(self._steps):
            if step.get_label() == label:
                self.nextstate_set(DEF_NEXTSTATE_OP.JUMP, index)
                return DEF_OK
        raise Exception(
            f"step with label '{label}' not found in procedure '{self.get_label()}'"
        )
        # self.nextstate_set(DEF_NEXTSTATE_OP.JUMP, idx)

    def nextstate_stop(self):
        self._is_running = False

    def nextstate_exit(self, msg=""):
        self.framework.call_shutdown(msg)

    def _increase_index(self):
        self._index += 1
        return self


class Procedures:
    def __init__(self) -> None:
        self.procedures: list["Procedure"] = []

    def add_procedure(self, new_procedure: Procedure):
        self.procedures.append(new_procedure)

    def get_procedure_by_label(self, label: str) -> Procedure | None:
        for procedure in self.procedures:
            if procedure.get_label() == label:
                return procedure
        return None
