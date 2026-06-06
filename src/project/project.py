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
    procedure, args = Utils.extract_step_interface(step_interface)
    test_cases = ["test1", "test2"]
    test_count = len(test_cases)
    index: int | None = procedure.session.attribute_get("index")

    if index == None:
        index = 0
        procedure.session.create({"test_cases": test_cases, **args})
    else:
        index += 1

    if not test_count:
        return "no test cases"

    if index >= test_count:
        # set nextstate as exit with msg "completed"
        return "test session completed"

    test_case = test_cases[index]
    procedure.session.attribute_set("test_case", test_case)
    procedure.session.attribute_set("index", index)
    procedure.session.db_update()

    return DEF_OK


def instruments_setup(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    scope: Scope = repository.get_instrument_by_label("scope")
    dmm: Dmm = repository.get_instrument_by_label("dmm")
    ps: PowerSupply = repository.get_instrument_by_label("ps")

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


def dut_setup(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    dut = Dut()
    dut.register_write(dut.REG1, 0xAA)
    dut.register_write(dut.REG2, 0xBB)
    dut.bit_write(
        dut.BIT0,
        dut.BIT_ON,
    )
    procedure.session.attribute_set("dut", dut)
    return DEF_OK


def dut_verify(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    dut: Dut = procedure.session.attribute_get("dut")
    dmm: Dmm = repository.get_instrument_by_label("dmm")
    reg1_val = dut.register_read(dut.REG1)

    # if True:
    procedure.nextstate_exit()

    return DEF_OK


def measurement_start(step_interface: StepInterface):

    scope: Scope = repository.get_by_label("scope")
    scope.stream_waveform_data_to_file_demo("waveform.bin")

    return DEF_OK


def my_worker(step_interface: StepInterface):
    """demonstrate a worker running in a separate thread."""
    procedure, args = Utils.extract_step_interface(step_interface)

    # simulate some work
    for i in range(3):
        time.sleep(0.5)
        logger.info(f"worker stage: {i} {args}")
    try:
        procedure.get_worker_from_active_step().set_complete()
    except:
        pass

    return None


def report(step_interface: StepInterface):
    return DEF_OK


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


# create test procedure by adding steps one by one
def create_procedure_with_builder(label) -> Procedure:

    template = ProcedureBuilder(label)

    # template.add_step_worker_start("my_worker1", my_worker, {"11": "world"})
    # template.add_step_worker_start("my_worker2", my_worker, {"22": "world"})
    # template.add_step_worker_start("my_worker3", my_worker, {"33": "world"})
    # template.add_step_worker_wait(10, "my_worker1")
    # template.add_step_worker_wait(10, "my_worker2")
    # template.add_step_worker_wait(10, "my_worker3")
    # template.add_step_function(create_session, {"hello22": "world33"}, "create_session")
    # template.add_step_function(instruments_setup, NOARG, "")
    # template.add_step_function(dut_setup, NOARG, "dut_setup")
    # template.add_step_function(dut_verify, NOARG, "dut_verify")
    # template.add_step_function(measurement_start, NOARG, "start_measure")
    # template.add_step_function(report, NOARG, "report")
    template.add_step_exit("SESSION COMPLETED")

    procedure = template.generate_procedure()

    return procedure
