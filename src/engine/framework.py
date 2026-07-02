from datetime import datetime
from pathlib import Path
import threading
import queue
import logging
import json
import time
from typing import Any

from engine.context import Context
from engine.logger import setup_logging
from engine.utils import Utils
from engine.constants import *
from engine.procedure import Procedure
from engine.db import database
from engine.server.server_main import run_server

PROCESSOR_SECONDS_DELAY = 0.2
DEF_Q_SIZE = 1_000_000

USE_LOGGING = True


class Framework:
    def __init__(self):
        self.q_eng: queue.Queue = self.q_create(DEF_Q_SIZE)
        self.q_log: queue.Queue = self.q_create(DEF_Q_SIZE)
        self.q_list: list[queue.Queue] = []
        self.event_shutdown = threading.Event()
        self._procedure_list: list["Procedure"] = []
        self._procedure_dict: dict[str, int] = {}
        self.context: Context = Context(self)
        self.db = database

        if USE_LOGGING:
            self.log_listener = setup_logging(self.q_log)
            self.logger = logging.getLogger("[framework]")

        self.engine_thread = Utils.thread_define("engineThread", self._thread_method)
        self.engine_thread.start()

    def get_label(self):
        return "framework 0.0.1"

    def _thread_method(self):
        INTERVAL_SECONDS = 0

        while not self.event_shutdown.is_set():
            time.sleep(PROCESSOR_SECONDS_DELAY)
            try:
                element = self.q_eng.get(block=False, timeout=INTERVAL_SECONDS * 1000)
                self._command_processor(element["command"], element["payload"])
            except queue.Empty:
                pass
            self._procedure_loop()

    def _command_processor(self, command, args={}):
        command = DEF_CMD(command)
        handler = self._command_handlers(command)
        if not callable(handler):
            raise Exception(f"invalid command: {command}")
        res = handler(args)
        args["result"] = res
        self.log(command, args)
        return

    def _command_handlers(self, func_name: DEF_CMD):
        def func(args):
            "null func"

        def procedure_init(args):
            pass

        def add_new_procedure(args={}):
            procedure: Procedure = args["procedure"]
            procedure_label = procedure.get_label()
            is_exist = self._procedure_dict.get(procedure_label)
            if is_exist != None:
                raise Exception(
                    f"Procedure with label '{procedure_label}' already exists."
                )
            procedure.framework_set(self)
            self._procedure_list.append(procedure)
            index = len(self._procedure_list) - 1
            self._procedure_dict[procedure_label] = index
            return DEF_OK

        def exit(args={}):
            self.log_listener.stop()
            self.log_listener
            self.event_shutdown.set()
            return DEF_OK

        def procedure_awake(args={}):
            # start_at = 0
            # sleep_seconds = 0
            procedure: Procedure = args["procedure"]
            start_at: float = args["start_at"]
            sleep_seconds: float = args["sleep_seconds"]
            now = self.get_time_monotonic()
            delta = now - start_at
            if delta > sleep_seconds:
                # TODO call q_eng.set("start_procedure",procedure)
                procedure.start()
            else:

                # q_timer.q_add_element(
                self.q_add_element(
                    DEF_CMD.PROCEDURE_AWAKE,
                    args,
                )
            # procedure.logger.info(f"--->>>> {procedure.get_label()}")
            return

        func_dict = {
            DEF_CMD.PROCEDURE_INIT: procedure_init,
            DEF_CMD.PROCEDURE_PLAY: func,
            DEF_CMD.PROCEDURE_PAUSE: func,
            DEF_CMD.PROCEDURE_APPEND: add_new_procedure,
            DEF_CMD.PROCEDURE_AWAKE: procedure_awake,
            DEF_CMD.EXIT: exit,
        }
        return func_dict[func_name]

    def _procedure_loop(self):
        for procedure in self._procedure_list:
            should_run = procedure.is_running()
            self._procedure_processor(procedure) if should_run else None

        return

    def _procedure_processor(self, procedure: Procedure):
        procedure.execution_processor(self)

    def q_add_element(self, element: DEF_CMD, args=None):
        self.q_eng.put(Utils.q_element_create(element.value, args))

    def call_shutdown(self, msg=""):
        self.q_add_element(DEF_CMD.EXIT)

    def log(self, command, args):
        command = DEF_CMD(command).value
        res = args["result"]
        params = {
            "params": {
                "command": command,
                "result": res,
            }
        }
        self.logger.info("CMD", extra=params)

    def procedure_append(self, procedure: Procedure):
        self.q_add_element(DEF_CMD.PROCEDURE_APPEND, {"procedure": procedure})

    def procedure_get_by_label(self, label) -> Procedure:
        index = self._procedure_dict[label]
        return self._procedure_list[index]

    def wait_shutdown(self):
        while not self.event_shutdown.is_set():
            time.sleep(0.5)

    def start_api_server(self):

        run_server()
        pass

    def q_create(self, size=1_000_000):
        q = queue.Queue(size)
        self.q_list.append(q)
        return q

    @staticmethod
    def get_time_monotonic():
        return time.monotonic()

    @staticmethod
    def get_time_datetime():
        return datetime.now()


framework = Framework()
