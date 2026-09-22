"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging

# from engine.framework import framework
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from project.project import Project
from project.template import *

logger = logging.getLogger("[user]")


class DutTest(Project):

    def __init__(self, config):

        super().__init__(config)

        dut_test = self.build_dut_test()
        USE_BASE_PROJECT = True
        if USE_BASE_PROJECT:
            final_procedure = self.project_export(config, dut_test)
        else:
            final_procedure = dut_test

        final_procedure.start()
        framework.procedure_append(final_procedure)

    def build_dut_test(self) -> Procedure:
        builder = ProcedureBuilder("dut_test")
        builder.step_call(self.runtime_dut_test)
        dut_test = builder.generate_procedure()
        return dut_test

    def runtime_dut_test(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        # self.init_repo_by_json()
        scope: Scope = repository.get_instrument_by_label("scope")
        dmm: Dmm = repository.get_instrument_by_label("dmm")
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
