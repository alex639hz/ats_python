"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

from datetime import datetime
from pathlib import Path
import threading
import queue
import logging
import json
import time
from typing import Any

from engine.procedure import Procedure
from engine.context import Context
from engine.logger import setup_logging
from engine.pipeline import Pipeline
from engine.constants import *
from engine.db import database
from engine.server.server_main import Server
from engine.utils import Utils

# from engine.server.server_main import run_server

DEF_Q_SIZE = 1_000_000

USE_LOGGING = True


class Framework:
    def __init__(self):
        # self.pipe_eng: queue.Queue = self.q_create(DEF_Q_SIZE)
        self.pipe_eng = Pipeline(DEF_Q_SIZE, "engine")
        self.pipe_timer = Pipeline(DEF_Q_SIZE, "timer")
        self.pipe_log = Pipeline(DEF_Q_SIZE, "timer")
        self.event_shutdown = threading.Event()
        self._procedure_list: list["Procedure"] = []
        self._procedure_dict: dict[str, int] = {}
        self.context: Context = Context(self)
        self.db = database
        self.server = Server()

        if USE_LOGGING:
            self.log_listener = setup_logging(self.pipe_log.get_pipe())
            self.logger = logging.getLogger("[framework]")

        self.engine_thread = Utils.thread_define("Engine", self._thread_engine)
        self.engine_timer = Utils.thread_define("Timer", self._thread_timer)

    def _thread_engine(self):
        PROCESSOR_RATE = 0.01

        while not self.event_shutdown.is_set():
            try:
                element = self.pipe_eng.element_pop(block=True, timeout=PROCESSOR_RATE)
                self._command_processor(element)
                continue
            except queue.Empty:
                pass
            self._procedure_loop()

    def _thread_timer(self):
        INTERVAL_SECONDS = 0.2
        arr = []
        while not self.event_shutdown.is_set():
            try:
                element = None
                element = self.pipe_timer.element_pop()
                is_ready = self.check_timer(element)
                if is_ready:
                    procedure: Procedure = element["payload"]["procedure"]
                    procedure.start()
                else:
                    arr.append(element)
                continue
            except queue.Empty:
                pass

            for waiting_element in arr:
                self.pipe_timer.element_push(
                    waiting_element["command"], waiting_element["payload"]
                )
            arr = []
            time.sleep(INTERVAL_SECONDS)

    def check_timer(self, element):
        # command = element["command"]
        payload = element["payload"]
        present_time = self.get_time_monotonic()
        start_at = payload["start_at"]
        future_time = start_at + payload["sleep_seconds"]

        return present_time >= future_time

    def start(self):
        self.engine_thread.start()
        self.engine_timer.start()

    def get_label(self):
        return "framework 0.0.1"

    def _command_processor(self, element):
        command = DEF_CMD(element["command"])
        payload = element["payload"]
        # command = DEF_CMD(command)
        handler = self._command_handlers(command)
        if not callable(handler):
            raise Exception(f"invalid command: {command}")
        res = handler(payload)
        return

    def _command_handlers(self, func_name: DEF_CMD):
        def func(args):
            return "null func"

        def procedure_init(args):
            pass

        def add_new_procedure(args={}):
            procedure: Procedure = args["procedure"]
            procedure_label = procedure.label
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

        def delete_procedure(args={}):
            procedure: Procedure = args["procedure"]
            procedure_label = procedure.label
            is_exist = self._procedure_dict.get(procedure_label)
            if is_exist == None:
                raise Exception(f"ERR delete_procedure: {procedure_label}")
            index = self._procedure_dict[procedure_label]
            del self._procedure_list[index]
            del self._procedure_dict[procedure_label]
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
                pass
            else:
                self.pipe_eng.element_push(
                    DEF_CMD.PROCEDURE_AWAKE,
                    args,
                )
            return

        def procedure_start(args={}):
            procedure: Procedure = args["procedure"]
            procedure.start()

            return

        func_dict = {
            DEF_CMD.PROCEDURE_INIT: procedure_init,
            DEF_CMD.PROCEDURE_START: procedure_start,
            DEF_CMD.PROCEDURE_PAUSE: func,
            DEF_CMD.PROCEDURE_APPEND: add_new_procedure,
            DEF_CMD.PROCEDURE_DELETE: delete_procedure,
            DEF_CMD.PROCEDURE_AWAKE: procedure_awake,
            DEF_CMD.FRAMEWORK_EXIT: exit,
        }
        return func_dict[func_name]

    def _procedure_loop(self):
        for procedure in self._procedure_list:
            should_run = procedure.is_running()
            self._procedure_processor(procedure) if should_run else None

        return

    def _procedure_processor(self, procedure: Procedure):
        procedure.execution_processor(self)

    # def q_add_element(self, element: DEF_CMD, args=None):
    # self.pipe_eng.put(Utils.q_element_create(element.value, args))

    def call_shutdown(self, msg=""):
        self.pipe_eng.element_push(DEF_CMD.FRAMEWORK_EXIT)

    def log_msg(self, msg, params={}):
        self.logger.info(msg, extra=params)

    def log_command(self, command, args):
        command = DEF_CMD(command).value
        # res = args["result"]
        params = {
            "params": {
                "command": command,
                # "result": res,
            }
        }
        self.logger.info("CMD", extra=params)

    def procedure_append(self, procedure: Procedure):
        self.pipe_eng.element_push(DEF_CMD.PROCEDURE_APPEND, {"procedure": procedure})

    def procedure_delete(self, procedure: Procedure):
        self.pipe_eng.element_push(DEF_CMD.PROCEDURE_DELETE, {"procedure": procedure})

    def procedure_get_by_label(self, label) -> Procedure:
        index = self._procedure_dict[label]
        return self._procedure_list[index]

    def wait_shutdown(self):
        while not self.event_shutdown.is_set():
            time.sleep(0.5)

    def start_api_server(self):
        self.server.run_server()
        pass

    @staticmethod
    def get_time_monotonic():
        return time.monotonic()

    @staticmethod
    def get_time_datetime():
        return datetime.now()


framework = Framework()
framework.start()
