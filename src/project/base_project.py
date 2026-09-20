"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging
import time

# from engine import utils
from engine.framework import framework
from engine.logger import create_log
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.constants import *

# from instruments.instrument import Instrument
from engine.utils import Utils
from project.instruments.instrument_repo import repository
from project.instruments.types.instrument_power_supply import PowerSupply
from project.instruments.types.instrument_dmm import Dmm
from project.instruments.types.instrument_scope import Scope
from project.libs.validation_session import DEF_PASS, ValidationSession
from project.presets.power_integrity import TestBuilderPowerSupply
from project.dut.dut_a import DutA
from project.template import *

LABEL_SESSION = "create_session"
LABEL_PREPARE_TEST = "prepare_test"
logger = logging.getLogger("[user]")


class BaseProject:
    def __init__(self) -> None:
        self.dut = DutA()

    def base_export(self, dut_test: Procedure):
        builder = ProcedureBuilder("dut_env_test")
        builder.step_call(self.runtime_create_session)
        builder.step_call(self.runtime_create_test, label="load_test")
        ENABLE_DUT_TEST = False
        if ENABLE_DUT_TEST:
            builder.insert_procedure(dut_test)
        builder.step_call(self.runtime_update_test_result)
        builder.step_call(self.runtime_loop_next)
        SHOULD_STOP_PROCEDURE = False
        SHOULD_EXIT_FRAMEWORK = True
        if SHOULD_STOP_PROCEDURE:
            builder.step_procedure_stop("procedure stop ...", "stop_procedure")
        elif SHOULD_EXIT_FRAMEWORK:
            builder.step_framework_exit("framework exit ...")

        env_setup = builder.generate_procedure()
        return env_setup

    def runtime_demo_init_once(self, step_interface: StepInterface):
        # return
        procedure, args = Utils.extract_step_interface(step_interface)
        step_label = procedure.get_active_step().label
        procedure.nextstate_next()
        return f"runtime_demo_init_once OK: {step_label}"

    def runtime_demo_init_in_loop(self, step_interface: StepInterface):
        # return
        procedure, args = Utils.extract_step_interface(step_interface)
        step_label = procedure.get_active_step().label
        # procedure.nextstate_wait_and_repeat(5)
        second_counter = procedure.context.attribute_get("second_counter") or 0
        second_counter += 1
        procedure.context.attribute_set("second_counter", second_counter)

        RUN_FOREVER = False
        if second_counter > 3 and not RUN_FOREVER:
            return

        procedure.nextstate_wait_and_repeat(1)
        return create_log(f"initialize in loop: {second_counter }", {"hello": "world"})

    def runtime_create_session(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        test_cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")
        session_init = {
            # "created_at": framework.get_time_datetime(),
            "label": procedure.label,
            "cases": test_cases,
        }
        session = ValidationSession(session_init)
        procedure.context.attribute_set("session", session)
        return f"session_id: {session.id}"

    def runtime_create_test(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        session: ValidationSession = procedure.context.attribute_get("session")
        session.load_test()
        return f"OK load_test index: {session.index}"

    def runtime_update_test_result(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        session: ValidationSession = procedure.context.attribute_get("session")
        test_case = session.get_active_case()
        if test_case["result"]:
            session.test_set_pass()
        else:
            session.test_set_fail()
        return DEF_OK

    def runtime_loop_next(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        session: ValidationSession = procedure.context.attribute_get("session")
        session.session_update_result()
        completed = not session.increase_index()

        if completed:
            # procedure.stop()
            return "COMPLETED"

        procedure.nextstate_jump_by_label("load_test")
        return f"going next test index: {session.index}"

    def runtime_verify_hw(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        def setup_env():

            def initialize_instruments(_path):
                path: Path = Path(_path)
                with path.open(encoding="utf-8") as f:
                    json_payload = json.load(f)

                # TODO does instrument_by_label required? check repository instead
                for instrument in json_payload:
                    repository.instrument_factory(instrument)

            initialize_instruments(f"C:/ats_python/src/project/instruments.json")
            dmm: Dmm = repository.get_instrument_by_label("dmm")
            ps: PowerSupply = repository.get_instrument_by_label("ps")

            dmm.setup()
            ps.setup()

        def setup_dut():
            self.dut.register_write(self.dut.REG1, self.dut.REG1_SETUP_C)
            self.dut.bit_write(self.dut.BIT0, self.dut.BIT_ON)

        # create_case()

        # setup_env()

        # setup_dut()

        return DEF_OK

    def get_thermal(self, degrees, label: str) -> Procedure:

        def thermal_read(step_interface: StepInterface):
            procedure, args = Utils.extract_step_interface(step_interface)

            thermal_counter = procedure.context.attribute_get("thermal_counter") or 0
            thermal_counter += 1
            procedure.context.attribute_set("thermal_counter", thermal_counter)

            RUN_FOREVER = False
            if thermal_counter > 3 and not RUN_FOREVER:
                procedure.context.attribute_set("status", "completed")
                procedure.stop()
                framework.procedure_delete(procedure)
                return

            procedure.context.attribute_set("status", "in_process")
            procedure.nextstate_wait_and_repeat(1)
            return f"degrees: {degrees}"

        builder = ProcedureBuilder(f"thermal_{label}")
        builder.step_call(thermal_read)
        builder.step_call(self.runtime_demo_init_in_loop, {"max_count": 3})
        recorder_procedure = builder.generate_procedure()
        SHOULD_START = True
        if SHOULD_START:
            recorder_procedure.start()
        SHOULD_APPEND = True
        if SHOULD_APPEND:
            framework.procedure_append(recorder_procedure)

        return recorder_procedure


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
