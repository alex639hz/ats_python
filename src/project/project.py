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


class Tester:

    def __init__(self, procedure: Procedure):
        self.procedure = procedure

    def get_active_test(self):
        pass


def create_session(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    test_cases = ["test1", "test2", "test3"]
    test_count = len(test_cases)

    if not test_count:
        return "no test cases"

    procedure.session.create({"test_cases": test_cases, **args})

    index = 0
    test_case = test_cases[index]
    procedure.session.attribute_set("index", index)
    procedure.session.attribute_set("test_case", test_case)
    procedure.session.attribute_set("test_cases", test_cases)

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
    # test_case = procedure.session.attribute_get("test_case")
    tester = Tester(procedure)
    procedure.session.attribute_set("tester", tester)
    return DEF_OK


def test_dut(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)
    test_case = procedure.session.attribute_get("test_case")
    scope: Scope = repository.get_by_label("scope")
    idn = scope.std_idn()
    # scope.stream_waveform_data_to_file_demo("waveform.bin")

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


def complete_session(step_interface: StepInterface):
    procedure, args = Utils.extract_step_interface(step_interface)

    tester: Tester = procedure.session.attribute_get("tester")
    procedure.logger.info(f"prepare_test: {tester.get_label()}")

    index = procedure.session.attribute_get("index")
    test_cases = procedure.session.attribute_get("test_cases")
    next_index = index + 1
    if next_index < len(test_cases):
        procedure.session.attribute_set("index", next_index)
        procedure.nextstate_jump_by_label("prepare_test")
        return "jump to next test case"

    return DEF_OK


# create test procedure by using test builder (preset mechanism)
def create_procedure_with_preset() -> Procedure:

    test = TestBuilderPowerSupply()
    test.step_init_test(create_session)
    test.step_setup_inst(instruments_setup)
    test.step_dut_setup(dut_setup_start)
    test.step_start_measurement(test_dut)
    test.step_generate_report(complete_session)
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

    builder.add_step_function(instruments_setup, NOARG, "")
    builder.add_step_function(dut_setup_start, NOARG, "dut_setup_start")
    builder.add_step_function(dut_setup_complete, NOARG, "dut_setup_complete")
    builder.add_step_function(create_session, NOARG, LABEL_CREATE_SESSION)
    builder.add_step_function(prepare_test, NOARG, "prepare_test")
    builder.add_step_function(test_dut, NOARG, "test_dut")
    builder.add_step_function(complete_session, NOARG, "complete_session")
    builder.add_step_exit("SESSION COMPLETED")
    return builder.generate_procedure()
