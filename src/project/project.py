import logging
from pathlib import Path
import time
from typing import Any

# from engine import utils
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.db import database
from engine.constants import *

# from instruments.instrument import Instrument
from engine.types import StepInterface
from engine.utils import Utils
from instruments.instrument_repo import repository
from instruments.types.instrument_power_supply import PowerSupply
from instruments.types.instrument_dmm import Dmm
from instruments.types.instrument_scope import Scope
from presets.power_integrity import TestBuilderPowerSupply
from project.dut import Dut

logger = logging.getLogger("[project]")


def create_session(step_interface: StepInterface):
    procedure, args = Utils.extract_function_interface(step_interface)
    procedure.session_create({"test_cases": ["test1", "test2"], **args})
    return DEF_OK


def instruments_setup(procedure: Procedure, args={}):
    session: dict[str, Any] = procedure.session_get()
    scope: Scope = repository.get_by_label_or_throw("scope")
    dmm: Dmm = repository.get_by_label_or_throw("dmm")
    ps: PowerSupply = repository.get_by_label_or_throw("ps")

    scope.set_waveform_metadata(
        source="CHAN1",
        format="WORD",
        byte_order="SWAP",
        points=1024,
        x_increment=1e-9,
        x_origin=0.0,
        y_increment=1.0,
        y_origin=0.0,
    )

    dmm.setup()
    ps.setup()

    return DEF_OK


def dut_setup(procedure: Procedure, args={}):

    session = procedure.session_get()
    dut = Dut()
    dut.register_write(dut.map.REG1, 0x01)
    dut.bit_write(
        dut.map.BIT0,
        True,
    )
    session["dut"] = dut
    procedure.session_set(session)
    return DEF_OK


def measurement_start(procedure: Procedure, args={}):

    scope: Scope = repository.get_by_label("scope")
    scope.stream_waveform_data_to_file_demo("waveform.bin")

    return DEF_OK


def my_worker(step_interface: StepInterface):
    """demonstrate a worker running in a separate thread."""
    procedure, args = Utils.extract_function_interface(step_interface)

    # simulate some work
    for i in range(10):
        time.sleep(0.5)
        logger.info(f"worker stage: {i} {args}")
    try:
        procedure.get_worker_from_active_step().set_complete()
    except:
        pass

    return None


def report(procedure: Procedure, args={}):
    return DEF_OK


# create test procedure by adding steps one by one
def create_procedure_with_builder(label) -> Procedure:

    template = ProcedureBuilder(label)

    template.add_step_worker_start("my_worker", my_worker, {"hello": "world"})
    template.add_step_function(create_session, {"hello22": "world33"}, "create_session")
    template.add_step_worker_wait("my_worker")
    # template.add_step_function(instruments_setup, NOARG, "setup_instruments")
    # template.add_step_function(dut_setup, NOARG, "setup_dut")
    # template.add_step_function(measurement_start, NOARG, "start_measure")
    # template.add_step_function(report, NOARG, "report")
    # template.add_step_exit()

    procedure = template.generate_procedure()

    return procedure


# create test procedure by using test builder (preset mechanism)
def create_procedure_with_preset() -> Procedure:

    test = TestBuilderPowerSupply()
    test.step_init_test(create_session)
    test.step_setup_inst(instruments_setup)
    test.step_dut_setup(dut_setup)
    test.step_start_measurement(measurement_start)
    test.step_generate_report(report)
    procedure = test.build("power supply test")

    return procedure
