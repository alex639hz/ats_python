import logging
import time
from typing import Any
from engine import procedure_builder
from engine.constants import NOARG
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.db import database

# from instruments.instrument import Instrument
from instruments.instrument_repo import repository
from instruments.types.instrument_power_supply import PowerSupply
from instruments.types.instrument_dmm import Dmm
from instruments.types.instrument_scope import Scope
from project.dut_a import DUT_BIT_INDEX, DUT_REG_ADDRESS, DutA, Register, DutRegisterMap

logger = logging.getLogger("[project]")

# example: create instruments instances
#######################################
#######################################

# ps3 = Instrument.aux_repo_get_by_label("ps3")

# many_ps_instances = Instrument.aux_repo_get_by_label_many(["ps1", "ps2", "ps3"])

#######################################
#######################################
#######################################
DEF_PROCEDURE_LABEL = "my_procedure"


def create_session(procedure: Procedure, args={}):

    procedure.session_create({"test_cases": ["test1", "test2"], **args})
    return f"create_session completed OK"


def fcall_template(procedure: Procedure, args={}):
    return f"fcall_template completed OK"


class SignalIntegrityTests:
    @staticmethod
    def eye_diagram_analysis(label: str) -> Procedure:
        """Eye Diagram Analysis — Assess signal integrity by analyzing eye diagrams for timing and voltage margins."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def jitter_measurement(label: str) -> Procedure:
        """Jitter Measurement — Evaluate the timing variations in the signal."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def rise_fall_time_validation(label: str) -> Procedure:
        """Rise/Fall Time Validation — Measure the time it takes for the signal to transition between logic levels."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def overshoot_undershoot_validation(label: str) -> Procedure:
        """Overshoot/Undershoot Validation — Check for excessive voltage excursions beyond the expected logic levels."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def ringing_validation(label: str) -> Procedure:
        """Ringing Validation — Assess the presence of oscillations in the signal."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def crosstalk_validation(label: str) -> Procedure:
        """Crosstalk Validation — Evaluate interference between adjacent signal lines."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def impedance_matching_validation(label: str) -> Procedure:
        """Impedance Matching Validation — Ensure the characteristic impedance of the transmission line matches the load impedance."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )

        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def receiver_sensitivity_validation(label: str) -> Procedure:
        """Receiver Sensitivity Validation — Measure the minimum input signal level that can be reliably detected."""

        procedure_template = ProcedureBuilder(label)
        procedure_template.add_step_function(
            fcall_template, NOARG, "pre-test configuration"
        )

        procedure = procedure_template.generate_procedure()

        return procedure
