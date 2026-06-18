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

LABEL_NONE = None 
LABEL_NAME = "__name__"
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
            builder.add_step_worker_start("my_worker1", self.my_worker, {"11": "world"})
            builder.add_step_worker_wait(
                "my_worker1", TIMEOUT_IN_SECONDS, "wait_worker1"
            )
        builder.add_step_function(self.runtime_pre_exec, NOARG, LABEL_NAME)
        builder.add_step_function(self.runtime_exec, NOARG, LABEL_NAME)
        builder.add_step_function(self.runtime_post_exec, NOARG, LABEL_NAME)
        builder.add_step_exit("SESSION COMPLETED")

        procedure = builder.generate_procedure().start()
        framework.procedure_append(procedure)

    def runtime_pre_exec(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        session_id = None 
        case_id = None

        def create_session(): 
            session = {
                "created_at": datetime.now(),
                "label": procedure.get_label(),
                "cases": self.cases,
            }
            res = procedure.db.insert_one(COLLECTION_SESSION, session)
            session_id = res.inserted_id

            procedure.context.attribute_set("session_id", session_id)
            procedure.context.attribute_set("session", session)

        def create_case():
            case = {
                "session_id": session_id,
                "case": self.case,
            }
            res = procedure.db.insert_one(COLLECTION_CASE, case)
            case_id = res.inserted_id

            procedure.context.attribute_set("case_id", case_id)
            procedure.context.attribute_set("case", case)

        def setup_env(): 
            dmm: Dmm = repository.get_instrument_by_label("dmm")
            ps: PowerSupply = repository.get_instrument_by_label("ps")

            dmm.setup()
            ps.setup()

        def setup_dut():
            self.dut.register_write(dut.REG1, dut.REG1_SETUP_C)
            self.dut.bit_write(dut.BIT0,dut.BIT_ON)

        # create session db
        ###################
        create_session()

        # create test db
        ################
        create_case()

        # instrument setup
        ##################
        setup_env()

        # dut setup
        ##################
        setup_dut()

        return DEF_OK

    def runtime_exec(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        scope: Scope = repository.get_instrument_by_label("scope")
        volt_rms = scope.measure_volt_rms()
        results = {
            "volt_rms":volt_rms
        }
        procedure.context.attribute_set("result",results)
        
    def runtime_post_exec(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        case_id = procedure.context.attribute_get("case_id")
        result = procedure.context.attribute_get("result")
        res = procedure.db.update_one(COLLECTION_CASE,{"_id":case_id},{"result":result})

    @staticmethod
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
