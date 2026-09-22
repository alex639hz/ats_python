"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging
import time

from engine.framework import framework
from engine.logger import create_log
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.constants import *
from engine.utils import Utils
from project.base_project import BaseProject
from project.presets.power_integrity import TestBuilderPowerSupply
from project.dut.dut_a import DutA
from project.template import *

logger = logging.getLogger("[user]")


class Project(BaseProject):

    def __init__(self, config):
        super().__init__(config)
        self.dut = DutA()

    def project_export(self, config, dut_test_):
        builder = ProcedureBuilder("project_alfa")
        builder.step_call(dut_test_)
        dut_project_procedure = builder.generate_procedure()
        # dut_test_procedure = self.build_dut_test(dut_test_)
        USE_BASE_PROJECT = True
        if USE_BASE_PROJECT:
            final_procedure = self.base_export(dut_project_procedure)
        else:
            final_procedure = dut_project_procedure

        return final_procedure

    # def build_dut_test(self, dut_test_):

    #     return dut_test

    def demo_build_automation_example_2(self):
        builder = ProcedureBuilder("dut_test")

        builder.step_call(self.runtime_demo_init_once)
        builder.step_call(self.runtime_start_thermal_read)
        builder.step_call(self.runtime_demo_init_in_loop)
        builder.step_call(self.runtime_demo_close_recorder)

        dut_test_procedure = builder.generate_procedure()

        SHOULD_USE_BASE_PROJECT = False
        if SHOULD_USE_BASE_PROJECT:
            # TODO fix below line
            # self.base_export(self.dut_init, self.dut_test)
            pass
        else:
            framework.procedure_append(dut_test_procedure)
            dut_test_procedure.start()

    def dut_init(self):
        dut = DutA()
        dut.open()
        dut.reg8_write(dut.REG1, 10)
        pass

    def runtime_start_thermal_read(self, step_interface: StepInterface):

        def thermal_read(step_interface: StepInterface):
            READ_INTERVAL_SECONDS = 2
            procedure, args = Utils.extract_step_interface(step_interface)
            step_label = procedure.get_active_step().label
            procedure.nextstate_wait_and_repeat(READ_INTERVAL_SECONDS)
            return f"proc:{procedure.label} step: {step_label}"

        procedure, args = Utils.extract_step_interface(step_interface)
        builder = ProcedureBuilder("thermal_recorder")
        builder.step_call(thermal_read)
        thermal_read_procedure = builder.generate_procedure()
        thermal_read_procedure.start()
        framework.procedure_append(thermal_read_procedure)
        framework.context.attribute_set("thermal_read", thermal_read_procedure)
        return f"proc:{procedure.label} runtime_demo_start_recorder"

    def runtime_demo_close_recorder(self, step_interface: StepInterface):
        # return
        # procedure, args = Utils.extract_step_interface(step_interface)
        # step_label = procedure.get_active_step().label
        # framework.log_msg(f"runtime_demo_close_recorder: {""}")
        thermal_read_procedure: Procedure = framework.context.attribute_get(
            "thermal_read"
        )
        thermal_read_procedure.stop()
        pass

    def runtime_dut_set_register(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        address = args["address"]
        value = args["value"]
        dut: DutA = procedure.context.attribute_get("dut")
        # dut.register_write(address, value)
        return f"write register address:{address} value{value}"

    def runtime_call_template(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        case = procedure.context.attribute_get("case")["case"]
        case_type = case["test_type"]
        case_label = case["label"]

        if case_type == "testA":
            template_a = TemplateA("test_A")
            case_procedure = template_a.get_procedure()
            framework.procedure_append(case_procedure)
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

    def get_waveform_procedure(self):
        scope: Scope = repository.get_instrument_by_label("scope")
        scope.get_waveform_single()

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
