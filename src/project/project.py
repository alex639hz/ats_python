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
SHOULD_EXPORT_BASE_PROJECT = True
logger = logging.getLogger("[user]")


class BaseProject:
    def __init__(self) -> None:
        self.framework = framework
        self.cases = Utils.read_json("C:/ats_python/src/project/test_cases.json")
        self.case_index = 0
        self.case = self.cases[self.case_index]
        self.dut = DutA()

    pass

    def export(self):
        builder = ProcedureBuilder("sub_proc_example")
        builder.step_call(self.runtime_init_env)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)
        builder.step_call(self.runtime_demo_step)

        procedure = builder.generate_procedure().start()
        self.framework.procedure_append(procedure)

    def runtime_demo_step(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        value = procedure.get_active_step().get_op().value
        print(f"hello: {value}")

        pass

    def runtime_init_env(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        created_at = self.framework.get_time_datetime()

        def create_session():
            session = {
                "created_at": created_at,
                "label": procedure.get_label(),
                "cases": self.cases,
            }
            res = procedure.db.insert_one(COLLECTION_SESSION, session)
            session["_id"] = res.inserted_id
            procedure.context.attribute_set("session", session)

        def create_case():
            session = procedure.context.attribute_get("session")
            session_id = session["_id"]
            selected_case = session["cases"][0]

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

        create_session()

        create_case()

        setup_env()

        setup_dut()

        return DEF_OK


class Project(BaseProject):

    def __init__(self) -> None:
        super().__init__()

        if SHOULD_EXPORT_BASE_PROJECT:
            self.export()

        builder = ProcedureBuilder("main_proc_example")

        EXAMPLE_2 = True
        if EXAMPLE_2:
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)
            builder.step_call(self.runtime_demo_step)

        procedure = builder.generate_procedure().start()
        self.framework.procedure_append(procedure)

    # def export(self):

    def runtime_demo_step_v2(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        value = procedure.get_active_step().get_op().value
        print(f"hello: {value}")
        WAIT_SECONDS = 3
        procedure.nextstate_next(WAIT_SECONDS)
        print(f"world: {value}")
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
