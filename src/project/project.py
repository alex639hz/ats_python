import logging
from pathlib import Path
import time
from typing import Any
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.db import database
from engine.constants import *

# from instruments.instrument import Instrument
from instruments.instrument_repo import repository
from instruments.types.instrument_power_supply import PowerSupply
from instruments.types.instrument_dmm import Dmm
from instruments.types.instrument_scope import Scope
from presets.power_integrity import TestBuilderPowerSupply
from project.dut import Dut

logger = logging.getLogger("[project]")


def create_session(procedure: Procedure, args={}):

    procedure.session_create({"test_cases": ["test1", "test2"], **args})
    return DEF_MSG_OK


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

    return DEF_MSG_OK


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
    return DEF_MSG_OK


def measurment_start(procedure: Procedure, args={}):

    scope: Scope = repository.get_by_label("scope")
    scope.stream_waveform_data_to_file_demo("waveform.bin")

    return DEF_MSG_OK


def example(procedure: Procedure, args={}):
    logger.info("Example step executed with args: %s", args)
    return None  # Note: returned data  from thread is ignored


def report(procedure: Procedure, args={}):
    return DEF_MSG_OK


def create_procedure_with_builder(label) -> Procedure:

    template = ProcedureBuilder(label)

    template.add_worker(example, {"hello": "world"}, "example_worker")
    template.add_worker_check("example_worker")
    # template.add_fcall(example, NOARG, "")
    # template.add_fcall(create_session, NOARG, "create_session")
    # template.add_fcall(instruments_setup, NOARG, "setup_instruments")
    # template.add_fcall(dut_setup, NOARG, "setup_dut")
    # template.add_fcall(measurment_start, NOARG, "start_measure")
    # template.add_fcall(report, NOARG, "report")
    # template.add_fexit()

    procedure = template.generate_procedure()

    return procedure


def create_procedure_with_preset() -> Procedure:

    test = TestBuilderPowerSupply()
    test.step_init_test(create_session)
    test.step_setup_inst(instruments_setup)
    test.step_dut_setup(dut_setup)
    test.step_start_measurement(measurment_start)
    test.step_generate_report(report)
    procedure = test.build("power supply test")

    return procedure
