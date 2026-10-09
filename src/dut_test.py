"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging

# from engine.framework import framework
from engine.constants import *
from engine.framework import framework
from engine.procedure_builder import ProcedureBuilder
from engine.types import StepInterface
from engine.utils import Utils
from project.project import Project

# from project.template import *

logger = logging.getLogger("[user]")


class DutTest(Project):

    def __init__(self, config):

        # super().__init__(config)

        dut_test = self.build_dut_test()
        USE_BASE_PROJECT = True
        if USE_BASE_PROJECT:
            final_procedure = self.project_export(dut_test)
        else:
            final_procedure = dut_test

        final_procedure.start()
        framework.procedure_append(final_procedure)

    def build_dut_test(self):
        dut_flow_build = ProcedureBuilder("dut_test")
        dut_flow_build.step_call(self.runtime_dut_test)
        dut_flow = dut_flow_build.generate_procedure()
        return dut_flow

    def runtime_dut_test(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        counter = procedure.context.attribute_get("counter", 0)
        counter = counter + 1
        procedure.context.attribute_set("counter", counter)
        msg = f"counter: {counter}"
        ONE_SECOND = 1
        MAX_SECONDS = 5
        if counter < MAX_SECONDS:
            procedure.nextstate_sleep_and_repeat(ONE_SECOND)
        else:
            msg = f"completed: {counter}"
            procedure.nextstate_exit()

        return msg
