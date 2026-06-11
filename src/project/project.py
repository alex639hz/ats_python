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


class Tester:

    def __init__(self, procedure: Procedure, cases):
        self.procedure = procedure
        self.index = 0
        self.cases = cases

    def get_active_case(self):
        return self.cases[self.index]

    def count(self):
        return len(self.cases)

    def complete_case(self):
        self.index += 1
        is_completed = self.index >= self.count()
        return is_completed


def create_session(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)

    test_cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")

    test_count = len(test_cases)

    if not test_count:
        return "no test cases"

    procedure.session.create({"test_cases": test_cases, **args})

    tester = Tester(procedure, test_cases)
    procedure.session.attribute_set(LABEL_TESTER, tester)

    return DEF_OK


def instruments_setup(step_interface: StepInterface):
    """setup instruments once or based on test case"""
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


def dut_setup_start(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    dut = Dut()

    dut.register_write(dut.REG1, dut.REG1_SETUP_C)
    dut.register_write(dut.REG2, dut.REG2_SETUP_A)
    dut.bit_write(
        dut.BIT0,
        dut.BIT_ON,
    )
    procedure.session.attribute_set("dut", dut)
    return DEF_OK


def dut_setup_complete(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    dut: Dut = procedure.session.attribute_get("dut")
    dmm: Dmm = repository.get_instrument_by_label("dmm")
    reg1_val = dut.register_read(dut.REG1)

    ERROR_DEMO = False
    if ERROR_DEMO:
        procedure.nextstate_exit("failed dut_verify")
        return

    return DEF_OK


def prepare_test(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)

    tester: Tester = procedure.session.attribute_get(LABEL_TESTER)
    case = tester.get_active_case()

    return f"$ {case} $"


def test_dut(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    tester: Tester = procedure.session.attribute_get(LABEL_TESTER)
    case = tester.get_active_case()
    volt_rms_max = case["vrms_max"]
    scope: Scope = repository.get_by_label("scope")
    volt_rms = scope.measure_volt_rms()
    if volt_rms > volt_rms_max:
        msg = "PASS"
    else:
        msg = "FAILED"
    procedure.logger.info(f"volt rms: {volt_rms}, {msg}")
    return DEF_OK


def my_worker(step_interface: StepInterface):
    """demonstrate a worker running in a separate thread."""
    procedure, args = Utils.extract_step_interface(step_interface)

    # simulate some work
    for i in range(3):
        time.sleep(0.5)
        procedure.logger.info(f"worker stage: {i}")
    try:
        procedure.get_worker_from_active_step().set_complete()
    except:
        pass

    return None


def complete_test_case(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)

    tester: Tester = procedure.session.attribute_get(LABEL_TESTER)
    cases_completed = tester.complete_case()
    if not cases_completed:
        procedure.nextstate_jump_by_label(LABEL_PREPARE_TEST)
        return DEF_OK

    return DEF_OK


# create test procedure by using test builder (preset mechanism)
def create_procedure_with_preset() -> Procedure:

    test = TestBuilderPowerSupply()
    test.step_init_test(create_session)
    test.step_setup_inst(instruments_setup)
    test.step_dut_setup(dut_setup_start)
    test.step_start_measurement(test_dut)
    test.step_generate_report(complete_test_case)
    procedure = test.build("power supply test")

    return procedure


# create test procedure by adding steps one by one
def create_procedure_with_builder(label: str) -> Procedure:
    builder = ProcedureBuilder(label)
    USE_WORKER = False
    if USE_WORKER:
        TIMEOUT_IN_SECONDS = 5
        builder.add_step_worker_start("my_worker1", my_worker, {"11": "world"})
        builder.add_step_worker_wait("my_worker1", TIMEOUT_IN_SECONDS, "wait_worker1")

    builder.add_step_function(create_session, NOARG, LABEL_CREATE_SESSION)
    builder.add_step_function(dut_setup_start, NOARG, "dut_setup_start")
    builder.add_step_function(dut_setup_complete, NOARG, "dut_setup_complete")
    builder.add_step_function(prepare_test, NOARG, LABEL_PREPARE_TEST)
    builder.add_step_function(instruments_setup, NOARG, "")
    builder.add_step_function(test_dut, NOARG, "test_dut")
    builder.add_step_function(complete_test_case, NOARG, "complete_test_case")
    builder.add_step_exit("SESSION COMPLETED")
    return builder.generate_procedure()
