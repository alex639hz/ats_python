from pathlib import Path
import threading
import queue
import logging
import json
import time

from engine.logger import empty_get_logger, empty_setup_logging, setup_logging
from engine.utils import Utils
from engine.constants import *
from engine.procedure import Procedure
from engine.db import database
from instruments.instrument_repo import repository
from instruments.instrument_factory import instrument_factory

DEF_ENG_INTERVAL_SECONDS = 0.001
DEF_Q_SIZE = 1_000_000

USE_JSON_INSTRUMENT = False
USE_LOGGING = True


class Framework:
    def __init__(
        self,
    ):
        # self.instruments_repo = self.repository
        self.q_eng: queue.Queue = queue.Queue(DEF_Q_SIZE)
        self.q_log: queue.Queue = queue.Queue(DEF_Q_SIZE)
        self.event_shutdown = threading.Event()
        self.procedure_list: list["Procedure"] = []
        self.procedure_dict: dict[str, int] = {}
        self.database = database

        if USE_LOGGING:
            self.log_listener = setup_logging(self.q_log)
            self.logger = logging.getLogger("[framework]")
        else:
            self.log_listener = empty_setup_logging()
            self.logger = empty_get_logger()

        if USE_JSON_INSTRUMENT:
            BASE_DIR = Path(__file__).resolve().parent / ".."
            path = BASE_DIR / "project" / "instruments.json"
            self.q_eng_add_element(DEF_CMD.INIT_INSTRUMENTS_FROM_JSON, {"path": path})

        self.engine_thread = Utils.thread_define("engineThread", self.thread_method)
        self.engine_thread.start()

    def thread_method(self):
        while not self.event_shutdown.is_set():
            try:
                element = self.q_eng.get(block=True, timeout=DEF_ENG_INTERVAL_SECONDS)
                command, args = Utils.q_element_get_params(element)
                self.command_processor(command, args)
            except queue.Empty:
                pass
            self.procedure_loop()

    def command_processor(self, command, args={}):
        command = DEF_CMD(command)
        handler = self.command_handlers(command)
        res = handler(args)
        self.log(command, res)
        return

    def procedure_loop(self):
        for procedure in self.procedure_list:
            should_run = procedure._is_running
            self.procedure_processor(procedure) if should_run else None

        return

    def procedure_processor(self, procedure: Procedure):
        procedure.execution_processor(self)
        procedure.nextstate_processor()

    def q_eng_add_element(self, element: DEF_CMD, args=None):
        self.q_eng.put(Utils.q_element_create(element.value, args))

    def call_shutdown(self):
        self.q_eng_add_element(DEF_CMD.EXIT)

    def log(self, command, res):
        command = DEF_CMD(command).value
        self.logger.info(f"[COMMAND]\t{command} -> {res}")

    def start(self):
        self.event_shutdown.set()

    def procedure_append(self, procedure: Procedure):
        self.q_eng_add_element(DEF_CMD.PROCEDURE_APPEND, {"procedure": procedure})

    def command_handlers(self, func_name: DEF_CMD):
        def func(args):
            pass

        def procedure_append(args={}):
            procedure: Procedure = args["procedure"]
            procedure_label = procedure.get_label()
            is_exist = self.procedure_dict.get(procedure_label)
            if is_exist is not None:
                raise Exception(
                    f"Procedure with label '{procedure_label}' already exists."
                )
            procedure.db_set(self.database)
            procedure.framework_set(self)
            self.procedure_list.append(procedure)
            index = len(self.procedure_list) - 1
            self.procedure_dict[procedure_label] = index
            return "procedure appended OK"

        def exit(args={}):
            # self.logger.info("exit app")
            self.log_listener.stop()
            self.event_shutdown.set()
            return DEF_OK

        def load_instruments_json(args={}):
            path: Path = args["path"]
            with path.open(encoding="utf-8") as f:
                json_payload = json.load(f)

            # TODO does instrument_by_label required? check repository instead
            for instrument in json_payload:
                instrument_factory(instrument)

            return "instruments initialized from json OK"

        func_dict = {
            DEF_CMD.INIT_INSTRUMENTS_FROM_JSON: load_instruments_json,
            DEF_CMD.PROCEDURE_PLAY: func,
            DEF_CMD.PROCEDURE_PAUSE: func,
            DEF_CMD.PROCEDURE_APPEND: procedure_append,
            DEF_CMD.EXIT: exit,
        }
        return func_dict[func_name]

    def run(self):
        while not self.event_shutdown.is_set():
            time.sleep(0.1)


framework = Framework()
