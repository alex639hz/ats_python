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

DEF_ENG_INTERVAL_SECONDS = 10
DEF_Q_SIZE = 1_000_000

USE_LOGGING = True


class Framework:
    def __init__(self):
        self.q_eng: queue.Queue = queue.Queue(DEF_Q_SIZE)
        self.q_log: queue.Queue = queue.Queue(DEF_Q_SIZE)
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
        while not self.event_shutdown.is_set():
            time.sleep(0.1)
            try:
                element = self.q_eng.get(
                    block=False, timeout=DEF_ENG_INTERVAL_SECONDS * 1000
                )
                command, args = Utils.q_element_get_params(element)
                self._command_processor(command, args)
            except queue.Empty:
                pass
            self._procedure_loop()

    def _command_processor(self, command, args={}):
        command = DEF_CMD(command)
        handler = self._command_handlers(command)
        if not callable(handler):
            raise Exception(f"invalid command: {command}")
        res = handler(args)
        self.log(command, res)
        return

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

    def log(self, command, res):
        command = DEF_CMD(command).value
        params = {
            "params": {
                "command": command,
                "response": res,
            }
        }
        self.logger.info("CMD", extra=params)

    def procedure_append(self, procedure: Procedure):
        self.q_add_element(DEF_CMD.PROCEDURE_APPEND, {"procedure": procedure})

    def _command_handlers(self, func_name: DEF_CMD):
        def func(args):
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
            params = {
                "params": {
                    "now": now,
                    "start_at": start_at,
                    "delta": delta,
                }
            }
            # self.logger.info("@@@@@", extra=params)
            if delta > sleep_seconds:
                procedure.start()
            else:
                self.q_add_element(
                    DEF_CMD.PROCEDURE_AWAKE,
                    args,
                )
            return

        func_dict = {
            DEF_CMD.PROCEDURE_PLAY: func,
            DEF_CMD.PROCEDURE_PAUSE: func,
            DEF_CMD.PROCEDURE_APPEND: add_new_procedure,
            DEF_CMD.PROCEDURE_AWAKE: procedure_awake,
            DEF_CMD.EXIT: exit,
        }
        return func_dict[func_name]

    def wait_shutdown(self):
        while not self.event_shutdown.is_set():
            time.sleep(0.5)

    def start_api_server(self):

        run_server()
        pass

    @staticmethod
    def get_time_monotonic():
        return time.monotonic()

    @staticmethod
    def get_time_datetime():
        return datetime.now()


framework = Framework()
