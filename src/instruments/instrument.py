# from http import server
import pyvisa
import threading
import queue
import logging
import types
import time
import numpy as np
from datetime import datetime
from typing import TYPE_CHECKING, List, cast
from io import BufferedWriter
from pathlib import Path
from pyvisa.resources import MessageBasedResource
from enum import Enum
from engine.globals import *
from engine.utils import Utils
from instruments.instrument_repo import repository
from instruments.instrument_type import InstrumentType

import instruments.virtual.virtual_instrument_server as v_server

if TYPE_CHECKING:
    from instruments.types.instrument_power_supply import PowerSupply
    from instruments.types.instrument_scope import Scope
    from instruments.types.instrument_dmm import Dmm

logger = logging.getLogger("[instrument]")

DEF_VISA_VIRTUAL = False
DEF_VISA_BACKEND = "pyvisa-py"
DEF_VERIFY_CONNECTION_AT_INIT = True
DEF_VISA_TIMEOUT_SECONDS = 60
DEF_STREAM_CHUNK_SIZE = 128
DEF_TERMINATION_NEWLINE = "\n"
DEF_TERMINATION_NONE = None
# DEF_READ_TERMINATION_QUERY = "\n"
# DEF_READ_TERMINATION_BIGQUERY = None
# DEF_WRITE_TERMINATION_CHAR = "\n"
DEF_SHOULD_LOG_SCPI = False
# TODO visa_resource_manager should be closed on app exit i.e. engine.close()
visa_resource_manager = pyvisa.ResourceManager()


class Instrument:

    class Models(Enum):
        DMM_MODEL_K2000 = "K2000"
        DMM_MODEL_K2100 = "K2100"
        DMM_MODEL_34401 = "34401"
        DMM_MODEL_OTHER = "DMM_MODEL_OTHER"
        POWER_SUPPLY_MODEL_OTHER = "POWER_MODEL_OTHER"

    class ScpiOperation(Enum):
        WRITE = "WRITE"
        QUERY = "QUERY"
        BIG_QUERY = "BIG_QUERY"

    def __init__(self, virtual_instrument={}):
        # super().__init__(self)
        self._label = virtual_instrument["label"]
        self._model = virtual_instrument.get("model")
        self._type = virtual_instrument.get("type")
        self._address = virtual_instrument.get("address")
        self._channel = virtual_instrument.get("channel") or 0
        self._virtual = virtual_instrument.get("virtual") or False
        self._virtual_port = virtual_instrument.get("virtual_port") or False
        self._use_thread = virtual_instrument.get("use_thread") or True
        self._idn = ""
        self._instruments_repo = repository
        self._lock = threading.Lock()

        if self._virtual:
            self.virtual_server_start_single()

        try:
            connection = visa_resource_manager.open_resource(self._address)
            self.connection = cast(MessageBasedResource, connection)

        except Exception as e:
            error_msg = f"VISA Open error: {self._label} " + str(e)
            logger.error(error_msg)
            raise Exception(error_msg)

        if not self.connection:
            error_msg = f"no connection with instrument: {self._label}"
            logger.debug(error_msg)
            raise Exception(error_msg)

        self.connection.read_termination = DEF_TERMINATION_NEWLINE
        self.connection.write_termination = DEF_TERMINATION_NEWLINE
        self.connection.chunk_size = DEF_STREAM_CHUNK_SIZE
        self.connection.timeout = (
            virtual_instrument.get("timeout") or DEF_VISA_TIMEOUT_SECONDS * 1000
        )

        if self._use_thread:
            self._q_req: queue.Queue = queue.Queue()
            self._stop_event = threading.Event()
            self._thread = Utils.thread_define(
                f"{self._label}Thread", self.thread_method
            )
            self._thread.start()

        if DEF_VERIFY_CONNECTION_AT_INIT:
            log_msg = self._idn = self.std_idn()
            if DEF_SHOULD_LOG_SCPI:
                logger.info(log_msg)

        repository.add(self)

    def request(
        self,
        scpi_cmd,
        callback=None,
        scpi_operation: Instrument.ScpiOperation | None = None,
    ):

        if scpi_operation == None:
            scpi_operation = Instrument.get_scpi_operation(scpi_cmd)

        scpi_req = (scpi_operation, scpi_cmd, callback)

        res = self._scpi_request(scpi_req)

        if callable(callback):
            callback(res)

        return res

    """_io_loop: Single-thread per instrument for VISA access. Handles blocking calls."""

    def thread_method(self):
        # TODO TBD what to do with connection errors? should repeat?
        while not self._stop_event.is_set():

            # TODO add timeout to allow signal thread about shutdown
            try:
                # Allow graceful shutdown
                scpi_req = self._q_req.get(timeout=0.5)
            except queue.Empty:
                continue

            if not scpi_req:
                break

            log_msg = self._scpi_request(scpi_req)
            if DEF_SHOULD_LOG_SCPI:
                logger.info(log_msg)

    def _scpi_request(self, scpi_req):
        # with self._lock:
        scpi_operation, scpi_cmd, callback = scpi_req

        res = "OK"
        if scpi_operation == Instrument.ScpiOperation.WRITE:
            self.connection.read_termination = DEF_TERMINATION_NEWLINE
            self.connection.write(scpi_cmd)  # type: ignore
            log_msg = f"{self._label} -> '{scpi_cmd}']'"
        elif scpi_operation == Instrument.ScpiOperation.QUERY:
            self.connection.read_termination = DEF_TERMINATION_NEWLINE
            res = self.connection.query(scpi_cmd)
            log_msg = f"{self._label} -> '{scpi_cmd}' -> '{res}]'"
        elif scpi_operation == Instrument.ScpiOperation.BIG_QUERY:

            bin_filepath = self._scpi_query_v1(scpi_req)
            log_msg = f"{self._label}\t{scpi_cmd}\t{str(bin_filepath)}"
        else:
            raise Exception("Unknown SCPI operation")

        if callable(callback):
            callback(res)

        return res

    def _scpi_query_v1(self, scpi_req):
        # with self._lock:
        scpi_operation, scpi_cmd, callback = scpi_req

        self.connection.read_termination = DEF_TERMINATION_NONE

        # TODO session context should be provided in the queue
        session = global_context.get_session()
        active_procedure = session.get(DEF_GLOBAL_SESSION_FIELDS.ACTIVE_PROCEDURE)

        # procedure_label = Utils.procedure_get_label(active_procedure)
        ##################################################################

        base_path1: str = global_context.get_field_by_section_and_key(
            DEF_GLOBAL_SECTIONS.PATHS,
            DEF_GLOBAL_PATHS.RECORDS_BASE_PATH,
        )

        session_label: str = (
            global_context.get_field_by_section_and_key(
                DEF_GLOBAL_SECTIONS.SESSION,
                DEF_GLOBAL_SESSION_FIELDS.SESSION_LABEL,
            )
            or "my-session"
        )

        ##################################################################

        now_ts = int(time.time())
        time_suffix = datetime.fromtimestamp(now_ts).strftime("%y_%m_%d_%H%M%S")

        base_filepath: Path = (
            Path(base_path1)
            # / session_label
            # / procedure_label
            # / time_suffix
            # / self._label
            / "data"
        )

        bin_filepath = base_filepath.with_suffix(".bin")
        bin_filepath.parent.mkdir(parents=True, exist_ok=True)

        ##################################################################

        with open(bin_filepath, "wb") as binary_file:
            self.connection.write(scpi_cmd)
            self.stream_scpi_to_binary(binary_file)

        INCLUDE_TEXT = False
        if INCLUDE_TEXT:
            # self.convert_bin_to_txt(bin_filepath, bin_filepath.with_suffix(".txt"))
            pass
        # log_msg = f"{self._label}\t{scpi_cmd}\t{str(bin_filepath)}"
        return bin_filepath

    # =================================================
    # convert_bin_to_txt
    # =================================================

    def stream_scpi_to_binary(
        self,  # pyvisa.resources.MessageBasedResource,
        outfile: BufferedWriter,
    ) -> None:
        """
        Read IEEE-488.2 binary block from a PyVISA instrument,
        stream it to a binary file, and print it as signed 8-bit integers.
        """

        # --- Read '#' ---
        hash_char = self.connection.read_bytes(1)
        if hash_char != b"#":
            raise ValueError(f"Expected binary block, got {hash_char!r}")

        # --- Read number of digits ---
        n_digits = int(self.connection.read_bytes(1))
        if n_digits <= 0:
            raise ValueError("Invalid binary block header")

        # --- Read payload length ---
        length_bytes = self.connection.read_bytes(n_digits)
        total_len = int(length_bytes.decode("ascii"))
        data_list = []
        # --- Stream payload ---
        remaining = total_len

        while remaining > 0:
            to_read = min(DEF_STREAM_CHUNK_SIZE, remaining)

            chunk = self.connection.read_bytes(to_read)
            outfile.write(chunk)

            # Parse as signed 8-bit integers
            byte = np.frombuffer(chunk, dtype=np.int8)
            data_list.extend(byte)
            # logger.info(byte)

            remaining -= len(chunk)

        outfile.flush()
        # for value in data_list:
        # logger.info(value)

    def std_request_q(self, scpi_cmd, callback=None):
        scpi_operation = Instrument.get_scpi_operation(scpi_cmd)
        scpi_req = (scpi_operation, scpi_cmd, callback)
        self._q_req.put(scpi_req)
        return None

    def request_str(self, cmd: str) -> str:
        return str(self.request(cmd))

    def request_int(self, cmd: str) -> int:
        return int(self.request(cmd))

    def request_float(self, cmd: str) -> float:
        return float(self.request(cmd))

    def std_idn(self, callback=None):
        return self.request("*IDN?", callback)

    def std_opc_query(self):
        return self.request("*OPC?")

    def std_opc(self):
        return self.request("*OPC")

    def std_wait(self):
        return self.request("*WAI")

    def std_esr(self):
        return self.request("*ESR?")

    def std_stb(self):
        return self.request("*STB?")

    def std_pder(self):
        return self.request(":PDER?")

    def std_rst(self):
        self.request("*RST")

    def std_cls(self):
        self.request("*CLS")

    def std_test(self, callback=None):
        return self.request("*TST?", callback)

    def api_rst_and_opc(self):
        self.std_rst()
        self.std_cls()
        res = self.std_opc_query()
        # logger.info(f"{self._label} reset completed")
        return res

    def virtual_server_start_single(self) -> None:

        def start_virtual_instrument() -> None:
            from instruments.virtual.virtual_instrument_factory import (
                virtual_instrument_factory,
            )

            virtual_instrument = virtual_instrument_factory(self)
            v_server.start_server(virtual_instrument)
            pass

        thread = Utils.thread_define(f"Virtual_{self._label}", start_virtual_instrument)
        thread.start()

    def close(self):
        self.connection.close()

    @staticmethod
    def get_scpi_operation(scpi_cmd) -> Instrument.ScpiOperation:
        is_query = Utils.is_scpi_query(scpi_cmd)
        is_big_query = Utils.is_scpi_big_query(scpi_cmd)

        # if is_big_query:
        #     return Instrument.ScpiOperation.BIG_QUERY
        if is_query:
            return Instrument.ScpiOperation.QUERY
        else:
            return Instrument.ScpiOperation.WRITE

    # TODO verify if needed: virtual_server_start_many
    @staticmethod
    def virtual_server_start_many(instruments: List[Instrument]) -> None:
        """
        Iterate over a list of instruments and start a thread for each virtual instrument.

        Args:
            instruments (List[Instrument]): The list of instruments.
        """

        def start_thread(instrument: Instrument) -> None:
            if instrument._virtual:
                thread = Utils.thread_define(
                    f"Virtual_{instrument._label}",
                    start_virtual_instrument,
                    (instrument,),
                )
                # thread = `threading.Thread`(
                #     target=start_virtual_instrument, args=(instrument,)
                # )
                thread.start()
            # else:
            # Handle non-virtual instruments as needed
            # print(f"Non-virtual instrument: {instrument.instrument_type}")

        def start_virtual_instrument(instrument: Instrument) -> None:
            # runpy.run_module(f"{instrument.instrument_type}")
            pass

        for instrument in instruments:
            start_thread(instrument)

    @staticmethod
    def aux_std_call_method_on_many(method_ref, instances):
        functions = Instrument.aux_std_get_func_refs_on_many(method_ref, instances)
        for func in functions:
            func()

    @staticmethod
    def aux_std_get_func_refs_on_many(method_ref, instances):

        if isinstance(method_ref, str):
            func_name = method_ref

        elif isinstance(method_ref, (types.FunctionType, types.MethodType)):
            func_name = method_ref.__name__

        else:
            raise TypeError(
                f"Unsupported type: {type(method_ref).__name__}. "
                "Expected str or method/function."
            )

        refs = []
        for instance in instances:
            method = getattr(instance, func_name)
            refs.append(method)

        return refs

    @staticmethod
    def aux_init_config(label, model, address):

        try:
            model = Instrument.Models(model)
            # except ValueError:
            # raise ValueError(f"Invalid step value: {step}")
        except Exception:
            pass

        # if not isinstance(step, (Steps, str)):
        # raise TypeError(f"Expected Steps or str, got {type(step)}")

        model_to_type_map = {
            Instrument.Models.DMM_MODEL_34401: InstrumentType.DMM,
            Instrument.Models.DMM_MODEL_K2000: InstrumentType.DMM,
            Instrument.Models.DMM_MODEL_K2100: InstrumentType.DMM,
            Instrument.Models.DMM_MODEL_K2100: InstrumentType.DMM,
            Instrument.Models.DMM_MODEL_OTHER: InstrumentType.DMM,
            Instrument.Models.POWER_SUPPLY_MODEL_OTHER: InstrumentType.PS,
        }

        instrument_type = model_to_type_map[model].value

        return {
            "label": label,
            "model": model,
            "type": instrument_type,
            "address": address,
        }

    @staticmethod
    def get_by_label(label=""):
        existing_instrument = repository.get_by_label(label)
        if not existing_instrument:
            raise Exception(f"instrument labeled: {label} not in repository")
        return existing_instrument

    @staticmethod
    def get_by_labels(labels=[]):
        instances = []
        for label in labels:
            instance = Instrument.get_by_label(label)
            instances.append(instance)
        return instances
