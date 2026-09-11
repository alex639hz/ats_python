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

    pass

    def base_export(self, dut_test: Procedure):
        self.procedure_env_setup = ProcedureBuilder("env_setup")
        # read validation config and set context(lab env, test cases)
        # create db session
        # set lab env (scope,dmm, thermal)
        # set dut (power calibration)
        # execute test
        # save test results in db
        # repeat for every test case
        self.procedure_env_setup.step_call(self.runtime_verify_hw)
        self.procedure_env_setup.step_call(self.runtime_create_session)
        self.procedure_env_setup.insert_procedure(dut_test)
        self.procedure_env_setup.step_call(self.runtime_set_thermal)

        env_setup = self.procedure_env_setup.generate_procedure()
        return env_setup
        # env_setup.start()
        # framework.procedure_append(env_setup)

    def runtime_session_init(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        value = procedure.get_active_step().get_op().value
        print(f"hello: {value}")
        procedure.nextstate_next(1)
        pass

    def runtime_create_session(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)

        session = {
            "created_at": self.framework.get_time_datetime(),
            "label": procedure.label,
            "cases": self.cases,
        }
        res = procedure.db.create_session(session)
        session["_id"] = res.inserted_id
        procedure.context.attribute_set("session", session)
        return f"create_session OK {session["_id"]}"

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
