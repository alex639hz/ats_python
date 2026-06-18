from datetime import datetime
import logging
import time

# from engine import utils
from engine import procedure
from engine.framework import Framework
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

LABEL_CREATE_SESSION = "create_session"
LABEL_PREPARE_TEST = "prepare_test"
LABEL_TESTER = "tester"

logger = logging.getLogger("[user]")


class Project:

    def __init__(self) -> None:
        self.cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")
        self.case_index = 0
        self.case = self.cases[self.case_index]
        self.dut = Dut()

    def export(self, framework: Framework):
        builder = ProcedureBuilder("label")
        builder.add_step_delay(1, "delay")
        USE_WORKER = True
        if USE_WORKER:
            TIMEOUT_IN_SECONDS = 5
            builder.add_step_worker_start("my_worker1", my_worker, {"11": "world"})
            builder.add_step_worker_wait(
                "my_worker1", TIMEOUT_IN_SECONDS, "wait_worker1"
            )
        builder.add_step_function(self._pre_execution, NOARG, "_pre_execution")
        # builder.add_step_function(self._execution, NOARG, "_execution")
        # builder.add_step_function(self._post_execution, NOARG, "_post_execution")
        builder.add_step_exit("SESSION COMPLETED")

        procedure = builder.generate_procedure().start()
        framework.procedure_append(procedure)

    def _pre_execution(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        # create session db
        ###################

        session = {
            "created_at": datetime.now(),
            "label": procedure.get_label(),
            "cases": self.cases,
        }
        res = procedure.db.insert_one("session", session)
        session_id = res.inserted_id

        procedure.context.attribute_set("session_id", session_id)
        procedure.context.attribute_set("session", session)

        # create test db
        ################

        case = {
            "session_id": session_id,
            "case": self.case,
        }
        res = procedure.db.insert_one("case", case)
        case_id = res.inserted_id

        procedure.context.attribute_set("case_id", case_id)
        procedure.context.attribute_set("case", case)

        # instrument setup
        ##################

        dmm: Dmm = repository.get_instrument_by_label("dmm")
        ps: PowerSupply = repository.get_instrument_by_label("ps")

        dmm.setup()
        ps.setup()

        return DEF_OK

    def _execution(self):
        pass

    def _post_execution(self):
        pass


def dut_setup_start(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    dut = Dut()

    dut.register_write(dut.REG1, dut.REG1_SETUP_C)
    dut.register_write(dut.REG2, dut.REG2_SETUP_A)
    dut.bit_write(
        dut.BIT0,
        dut.BIT_ON,
    )
    procedure.context.attribute_set("dut", dut)
    return DEF_OK


def my_worker(step_interface: StepInterface):
    """demonstrate a worker running in a separate thread."""
    procedure, args = Utils.extract_step_interface(step_interface)
    path = LOG_FOLDER / f"test.log"

    import json

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            logger.info("hello worker " + record["level"])

    # simulate some work
    for i in range(3):
        time.sleep(0.5)
        logger.info(f"worker stage: {i}")
    try:
        procedure.get_worker_from_active_step().set_complete()
    except:
        pass

    return None


def create_procedure_with_preset() -> Procedure:
    def my_func():
        pass

    test = TestBuilderPowerSupply()
    test.step_init_test(my_func)
    test.step_setup_inst(my_func)
    test.step_dut_setup(my_func)
    test.step_start_measurement(my_func)
    test.step_generate_report(my_func)
    procedure = test.build("power supply test")

    return procedure


def instruments_setup(step_interface: StepInterface):
    """setup instruments once or based on test case"""
    procedure, args = Utils.extract_step_interface(step_interface)
    scope: Scope = repository.get_instrument_by_label("scope")
    dmm: Dmm = repository.get_instrument_by_label("dmm")
    ps: PowerSupply = repository.get_instrument_by_label("ps")

    dmm.setup()
    ps.setup()

    return DEF_OK
