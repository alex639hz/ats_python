from datetime import datetime
from time import time
from typing import TYPE_CHECKING
import logging


from engine.constants import *
from engine.utils import *
from engine.step import Step
from engine.worker import Worker

from engine.db import Db, database

if TYPE_CHECKING:
    from engine.framework import Framework


class Procedure:

    def __init__(self, label):
        self._label: str = label
        self._steps: list["Step"] = []
        self._vars = {}
        self._session: dict[str, Any] = {}
        self._session_id = ""
        self._index = 0
        self._is_running = False
        self._is_first_run = True
        self._nextstate = self.init_nextstate()
        self._db: Db
        self._framework: Framework
        self.logger = logging.getLogger("[procedure]")

    def db_set(self, database: Db):
        self._db = database
        return self

    def framework_set(self, fw: Framework):
        self._framework = fw
        return self

    def session_create(self, session_args: dict[str, Any] = {}, insert_db=True):
        """Creates a session for the procedure.
        The session dictionary stored in the procedure instance and used as data store during procedure execution.
        The session can be stored in the database if insert_db is True.
        """
        session = {
            "created_at": datetime.now(),
            "procedure_label": self.get_label(),
            **session_args,
        }

        if insert_db:
            res = self._db.insert_one("session", session)
            self._session_id = res.inserted_id

        self._session = session

        return session

    def session_db_update(self):
        _id = self._session_id
        session = self._session
        if not _id:
            raise Exception("session_id is not set, cannot update session in db")

        res = self._db.update_one("session", {"_id": _id}, {**session})

        return res

    def session_set(self, session_data={}, include_db=False):
        """Sets the session data for the procedure."""
        self._session = session_data
        if include_db:
            self.session_db_update()

    def session_get(self):
        return self._session

    def session_var_set(self, var_name, var_value):
        """Sets the session data for the procedure."""
        self._session[var_name] = var_value
        return self

    def session_var_get(self, var_name) -> Any:
        return self._session.get(var_name)

    def get_worker_from_active_step(self) -> Worker:
        """return worker reference from procedure session. This function valid ONLY for WORKER_START step"""
        step_args = self.get_active_step().get_args()
        worker_name = step_args.get(STEP_ARG.TITLE)  # [STEP_ARG.TITLE]
        if not worker_name:
            raise Exception(f"missing worker in active step")
        worker: Worker | None = self.session_var_get(worker_name)
        if not worker:
            raise Exception(f"missing worker in active step")
        return worker

    def execution_processor(self, framework: Framework):
        step = self.get_active_step()
        self.nextstate_next()  # Default nextstate is next, can be changed by step function
        try:
            res = step.func(self)
        except Exception as e:
            msg = f"step exception: {step.get_label() or step.func.__name__} {e}"
            self.nextstate_exit(msg)
            return

        if res:
            step.log(self, res)
        return

    def set_variable(self, key, value):
        self._vars[key] = value
        return self

    def get_variable(self, key):
        return self._vars.get(key)

    def step_append(self, step: Step):
        self._steps.append(step)
        return self

    def steps_count(self):
        return len(self._steps)

    def get_step_by_index(self, index: int) -> Step:
        return self._steps[index]

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

    def get_run(self):
        return self._is_running

    def start(self):
        self._is_running = True
        return self

    def stop(self):
        self._is_running = False
        return self

    def nextstate_processor(self):

        final_index = self.steps_count() - 1
        nextstate_op = self._nextstate[0]
        nextstate_idx = self._nextstate[1]
        is_index_range_ok = self._index < final_index
        is_index_range_error = self._index >= final_index

        if nextstate_op == DEF_NEXTSTATE_OP.NEXT and is_index_range_ok:
            self.increase_index()
        elif nextstate_op == DEF_NEXTSTATE_OP.NEXT and is_index_range_error:
            self.stop()
        elif nextstate_op == DEF_NEXTSTATE_OP.STAY:
            pass
        elif nextstate_op == DEF_NEXTSTATE_OP.PAUSE:
            self.increase_index().stop()
        elif nextstate_op == DEF_NEXTSTATE_OP.JUMP:
            self._index = nextstate_idx
        elif nextstate_op == DEF_NEXTSTATE_OP.ERROR:
            pass
        else:
            raise Exception(f"Undefined nextstate_op: {nextstate_op}")

        self.init_nextstate()

        return self

    def init_nextstate(self):
        self._nextstate = (DEF_NEXTSTATE_OP.PAUSE, 0)
        return self._nextstate

    def nextstate_set(self, nextstate_op: DEF_NEXTSTATE_OP, idx=0):
        self._nextstate = (nextstate_op, idx)

    def nextstate_next(self):
        self.nextstate_set(DEF_NEXTSTATE_OP.NEXT)

    def nextstate_stay(self):
        self.nextstate_set(DEF_NEXTSTATE_OP.STAY)

    def nextstate_jump(self, idx: int):
        self.nextstate_set(DEF_NEXTSTATE_OP.JUMP, idx)

    def nextstate_stop(self):
        self._is_running = False

    def nextstate_exit(self, msg=""):
        self._framework.logger.info(f"exit by '{self.get_label()}' {msg}")
        self._framework.call_shutdown()

    def increase_index(self):
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
