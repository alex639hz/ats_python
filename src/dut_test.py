"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging

# from engine.framework import framework
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from project.project import Project
from project.template import *

logger = logging.getLogger("[user]")


class DutTest(Project):

    def __init__(self, config) -> None:

        super().__init__(config)

        dut_test = self.build_test_procedure()
        USE_BASE_PROJECT = False
        if USE_BASE_PROJECT:
            final_procedure = self.project_export(dut_test)
        else:
            final_procedure = dut_test

        final_procedure.start()
        framework.procedure_append(final_procedure)

    def build_test_procedure(self):
        builder = ProcedureBuilder("dut_test")
        builder.step_call(
            self.runtime_dut_set_register,
            {"address": DutA.REG1, "value": DutA.REG1_SETUP_A},
        )
        builder.step_call(self.runtime_start_thermal_read)
        builder.step_call(self.runtime_dut_test)
        dut_test = builder.generate_procedure()
        return dut_test

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
        dut.register_write(dut.REG1, 10)
        pass

    def runtime_dut_test(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        is_first_run = procedure.is_first_run()
        if is_first_run:
            thermal = self.get_thermal(25, "starter")
            procedure.context.attribute_set("thermal", thermal)

        thermal: Procedure = procedure.context.attribute_get("thermal")

        status = thermal.context.attribute_get("status")
        # if status == "in_process":
        if status == "completed":
            # procedure.nextstate_wait_and_repeat(1)
            # thermal = procedure.context.attribute_delete("thermal")

            procedure.reset_is_first_run()
            return f"www ---completed---- {status}"

        procedure.nextstate_wait_and_repeat(1)
        return f"www {status}"
