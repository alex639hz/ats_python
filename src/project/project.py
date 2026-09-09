"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging
import time

# from engine import utils
from engine.framework import framework
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.constants import *

# from instruments.instrument import Instrument
from engine.utils import Utils
from project.instruments.instrument_repo import repository
from project.instruments.types.instrument_power_supply import PowerSupply
from project.instruments.types.instrument_dmm import Dmm
from project.instruments.types.instrument_scope import Scope
from project.presets.power_integrity import TestBuilderPowerSupply
from project.dut.dut_a import DutA
from project.template import *

LABEL_SESSION = "create_session"
LABEL_PREPARE_TEST = "prepare_test"
logger = logging.getLogger("[user]")


class BaseProject:
    def __init__(self) -> None:
        self.framework = framework
        self.cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")
        self.case_index = 0
        self.dut = DutA()

        self.procedure_env_setup = ProcedureBuilder("env_setup")

    pass

    def base_export(self, runtime_dut_init, runtime_test):

        self.procedure_env_setup.step_call(self.runtime_verify_hw)
        self.procedure_env_setup.step_call(self.create_session)
        self.procedure_env_setup.step_call(runtime_dut_init)
        self.procedure_env_setup.step_call(self.runtime_set_thermal)
        self.procedure_env_setup.step_call(runtime_test)

        env_setup = self.procedure_env_setup.generate_procedure()
        env_setup.start()
        framework.procedure_append(env_setup)

    def runtime_session_init(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        value = procedure.get_active_step().get_op().value
        print(f"hello: {value}")
        procedure.nextstate_next(1)
        pass

    def create_session(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        session = {
            "created_at": self.framework.get_time_datetime(),
            "label": procedure.get_label(),
            "cases": self.cases,
        }
        res = procedure.db.create_session(session)
        session["_id"] = res.inserted_id
        procedure.context.attribute_set("session", session)

    def runtime_set_thermal(self, step_interface: StepInterface):
        pass

    def runtime_verify_hw(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        def create_case():
            session = procedure.context.attribute_get("session")
            session_id = session["_id"]
            selected_case = session["cases"][0]
            created_at = self.framework.get_time_datetime()

            case = {
                "created_at": created_at,
                "session_id": session_id,
                "case": selected_case,
            }
            res = procedure.db.insert_one(COLLECTION_CASE, case)
            case_id = res.inserted_id
            procedure.context.attribute_set("case_id", case_id)
            procedure.context.attribute_set("case", case)

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


class Project(BaseProject):

    def __init__(self) -> None:
        super().__init__()

        builder = ProcedureBuilder("dut_test")

        builder.step_call(self.runtime_demo_init_once)
        builder.step_call(self.runtime_demo_start_recorder)
        builder.step_call(self.runtime_demo_init_in_loop)
        builder.step_call(self.runtime_demo_step_v4)

        dut_test_procedure = builder.generate_procedure()

        SHOULD_USE_BASE_PROJECT = False
        if SHOULD_USE_BASE_PROJECT:
            self.base_export(self.dut_init, self.dut_test)
        else:
            framework.procedure_append(dut_test_procedure)
            dut_test_procedure.start()

    def dut_init(self):
        pass

    def dut_test(self):
        pass

    def runtime_demo_init_once(self, step_interface: StepInterface):
        # return
        procedure, args = Utils.extract_step_interface(step_interface)
        step_label = procedure.get_active_step().get_label()
        framework.log_msg(f"initialize all that can be set in one call: {step_label}")
        procedure.nextstate_next()
        pass

    def runtime_demo_init_in_loop(self, step_interface: StepInterface):
        # return
        procedure, args = Utils.extract_step_interface(step_interface)
        step_label = procedure.get_active_step().get_label()
        # procedure.nextstate_wait_and_repeat(5)
        second_counter = procedure.context.attribute_get("second_counter") or 0
        second_counter += 1

        if second_counter > 5:
            return

        procedure.context.attribute_set("second_counter", second_counter)
        framework.log_msg(f"initialize in loop: {second_counter }")
        procedure.nextstate_wait_and_repeat(3)
        pass

    def runtime_demo_start_recorder(self, step_interface: StepInterface):
        # return

        def thermal_read(step_interface: StepInterface):
            procedure, args = Utils.extract_step_interface(step_interface)
            step_label = procedure.get_active_step().get_label()
            framework.log_msg(f"initialize all 8888888: {step_label}")
            procedure.nextstate_wait_and_repeat(1)

        builder = ProcedureBuilder("thermal_recorder")
        builder.step_call(thermal_read)
        recorder_procedure = builder.generate_procedure()
        framework.procedure_append(recorder_procedure)
        recorder_procedure.start()
        framework.context.attribute_set("recorder_procedure", recorder_procedure)
        pass

    def runtime_demo_step_v4(self, step_interface: StepInterface):
        # return
        # procedure, args = Utils.extract_step_interface(step_interface)
        # step_label = procedure.get_active_step().get_label()
        framework.log_msg(f"^^^^^^^ hello v4 step_label: {""}")
        # procedure.nextstate_wait_and_repeat(5)
        # procedure.nextstate_wait_and_next(5)
        recorder_procedure: Procedure = framework.context.attribute_get(
            "recorder_procedure"
        )
        recorder_procedure.stop()
        pass

    def runtime_call_template(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        case = procedure.context.attribute_get("case")["case"]
        case_type = case["test_type"]
        case_label = case["label"]

        if case_type == "testA":
            template_a = TemplateA("test_A")
            case_procedure = template_a.get_procedure()
            self.framework.procedure_append(case_procedure)
            self.test_proc = case_procedure
        else:
            raise Exception("case type error")
            # self.framework.context.attribute_set("case_procedure", case_procedure)

    def runtime_exec(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        test_a = procedure.framework.procedure_get_by_label("test_A")
        is_running = test_a.is_running()
        if is_running:
            procedure.nextstate_stay()
            return

        res = test_a.context.attribute_get("result")
        pass

    def runtime_post_exec(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        case_id = procedure.context.attribute_get("case_id")
        result = procedure.context.attribute_get("result")
        res = procedure.db.update_one(
            COLLECTION_CASE, {"_id": case_id}, {"result": result}
        )

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
