from engine.constants import *
from engine.procedure_builder import ProcedureBuilder
from project.types import *
from engine.utils import *
from engine.framework import framework


class TemplateA:

    def __init__(self, label):
        self.reg_store: dict[Any, int] = {}
        self.name = label

    def get_procedure(self):
        case_builder = ProcedureBuilder(self.name)
        case_builder.add_step_function(self.runtime_set_thermal, NOARG, LABEL_NAME)
        # case_builder.add_step_function(self.runtime_set_dut, NOARG, LABEL_NAME)
        # case_builder.add_step_function(self.runtime_measure, NOARG, LABEL_NAME)
        # case_builder.add_step_exit(f"COMPLETED")

        case_procedure = case_builder.generate_procedure().start()
        return case_procedure
        # self.framework.procedure_append(case_procedure)
        # self.framework.context.attribute_set("case_procedure", case_procedure)

    def runtime_set_thermal(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        # start_at_key = "start_At"
        # start_at = procedure.context.attribute_get(start_at_key)
        # if start_at == None:
        # start_at = datetime.now()
        # else:
        # start_at += 1

        # procedure.context.attribute_set(start_at_key, start_at)
        start_at = procedure.context.attribute_get("start_at")

        if start_at == None:  # first run
            start_at = framework.get_time_monotonic()
            procedure.context.attribute_set("start_at", start_at)

        ITERATIONS = 5
        final = start_at + ITERATIONS

        now = framework.get_time_monotonic()

        if now < final:
            procedure.nextstate_stay(sleep_seconds=1)
            return "WAITING"

        procedure.nextstate_next()
        return DEF_OK
