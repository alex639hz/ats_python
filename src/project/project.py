from datetime import datetime
import logging
import time

# from engine import utils
from engine import procedure
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


class Tester:

    def __init__(self, procedure: Procedure, cases):
        self.procedure = procedure
        self.procedure.context.create({"test_cases": cases})
        self.index = 0
        self.cases = cases

    def initialize(self):
        self.procedure.context.attribute_set(LABEL_TESTER, self)

    def get_active_case(self):
        return self.cases[self.index]

    def count(self):
        return len(self.cases)

    def complete_case(self):
        self.index += 1
        is_completed = self.index >= self.count()
        return is_completed

    def get_session(self):
        res_session = {
            "created_at": self.procedure.context.attribute_get("created_at"),
            "owner_label": self.procedure.context.attribute_get("owner_label"),
            "test_cases": self.procedure.context.attribute_get("test_cases"),
        }
        return {}


def create_session(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)

    test_cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")

    test_count = len(test_cases)

    if not test_count:
        return "no test cases"

    tester = Tester(procedure, test_cases)
    tester.initialize()
    db_session = {
        "created_at": datetime.now(),
        "owner_label": procedure.get_label(),
        "test_cases": test_cases,
    }
    res = procedure.db.insert_one("session", db_session)
    _id = res.inserted_id
    procedure.context.attribute_set("session_id", _id)
    return f"{_id} " + DEF_OK


def prepare_test(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)

    tester: Tester = procedure.context.attribute_get(LABEL_TESTER)
    case = tester.get_active_case()

    return f"$ {case} $"


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


def dut_setup_complete(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    dut: Dut = procedure.context.attribute_get("dut")
    dmm: Dmm = repository.get_instrument_by_label("dmm")
    reg1_val = dut.register_read(dut.REG1)

    ERROR_DEMO = False
    if ERROR_DEMO:
        procedure.nextstate_exit("failed dut_verify")
        return

    return DEF_OK


def test_dut(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    tester: Tester = procedure.context.attribute_get(LABEL_TESTER)
    case = tester.get_active_case()
    volt_rms_max = case["volt_rms_max"]
    scope: Scope = repository.get_by_label("scope")
    volt_rms = scope.measure_volt_rms()
    procedure.context.attribute_push("volt_rms_buffer", volt_rms)
    if volt_rms > volt_rms_max:
        msg = "PASS"
    else:
        msg = "FAILED"
    # procedure.logger.info(f"volt rms: {volt_rms}, {msg}")
    return f"volt rms: {volt_rms}, {msg}"


def my_worker(step_interface: StepInterface):
    """demonstrate a worker running in a separate thread."""
    procedure, args = Utils.extract_step_interface(step_interface)
    path = LOG_FOLDER / f"test.log"

    import json

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            print(record["level"])

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

    test = TestBuilderPowerSupply()
    test.step_init_test(create_session)
    test.step_setup_inst(instruments_setup)
    test.step_dut_setup(dut_setup_start)
    test.step_start_measurement(test_dut)
    test.step_generate_report(complete_test_case)
    procedure = test.build("power supply test")

    return procedure

class Project():
    def __init__(self):
        self.test = {} 
        self.builder = ProcedureBuilder("label")
        self.cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")
        self.case = cases[0]
        self.dut = Dut()


    def build():
        USE_WORKER = True
        if USE_WORKER:
            TIMEOUT_IN_SECONDS = 5
            self.builder.add_step_worker_start("my_worker1", my_worker, {"11": "world"})
            self.builder.add_step_worker_wait("my_worker1", TIMEOUT_IN_SECONDS, "wait_worker1")

        self.builder.add_step_delay(1, "delay")
        self.builder.add_step_function(self._create_test, {"case": case}, None)
        self.builder.add_step_function(self._create_env, NOARG, None)
        # self.builder.add_step_function(prepare_test, NOARG, LABEL_PREPARE_TEST)
        # self.builder.add_step_function(dut_setup_start, NOARG, "dut_setup_start")
        # self.builder.add_step_function(dut_setup_complete, NOARG, "dut_setup_complete")
        # self.builder.add_step_function(instruments_setup, NOARG, "instruments_setup")
        # self.builder.add_step_function(test_dut, NOARG, "test_dut")
        # self.builder.add_step_function(complete_test_case, NOARG, "complete_test_case")
        self.builder.add_step_exit("SESSION COMPLETED")
        return builder.generate_procedure()

    def _create_test(self,step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        case = args["case"]
        procedure.context.create({"case": case})
    
    def _create_env(self,step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        case = procedure.context.attribute_get("case")
        ps: PowerSupply = repository.get_instrument_by_label("ps")
        ps.setup(case)



    def _measure(self,step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        case = args["case"]

        scope: Scope = repository.get_instrument_by_label("scope")
        dmm: Dmm = repository.get_instrument_by_label("dmm")

        channel = case["channel"]
        dmm_read = dmm.read(channel)
        dut_read = dut.register_read(dut.REG2)
            
        procedure.context.attribute_set("dmm_read":dmm_read)
        procedure.context.attribute_set("dut_read":dut_read)

        results = procedure.context.get_context() 
        procedure.db.insert_one("test",results)

        