from typing import Callable
from engine.constants import *
from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder


def func():
    pass


class TestPowerIntegrityStatics:

    @staticmethod
    def supply_voltage(label: str) -> Procedure:
        """Supply Voltage Accuracy — Verify the DC voltage at the load matches the specified nominal value."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "setup test")
        procedure_template.step_call(func, NOARG, "setup instruments")
        procedure_template.step_call(func, NOARG, "setup dut")
        procedure_template.step_call(func, NOARG, "trigger measurement")
        procedure_template.step_call(func, NOARG, "collect data")
        procedure_template.step_call(func, NOARG, "store results")
        procedure_template.step_call(func, NOARG, "data analysis")
        procedure_template.step_call(func, NOARG, "report generation")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def voltage_ripple_and_noise(label: str) -> Procedure:
        """Voltage Ripple & Noise — Quantify AC variations on the power rail to ensure they don’t violate noise margins."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def load_transient_response(label: str) -> Procedure:
        """Load Transient Response — Measure voltage droop/overshoot when current changes rapidly (load steps)."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def ir_drop_validation(label: str) -> Procedure:
        """IR Drop Validation — Measure voltage loss from source to load under current to ensure it stays within limits."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def powerrail_sequencing(label: str) -> Procedure:
        """Power Rail Sequencing** — Verify rails power up/down in the correct order and timing per spec."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def powersupply_rejection_ratio(label: str) -> Procedure:
        """PSRR (Power Supply Rejection Ratio) — Evaluate how well the system rejects noise from the power supply"""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def decoupling(label: str) -> Procedure:
        """Decoupling Effectiveness — Validate that capacitors suppress high-frequency noise on the rail."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def impedance_profile(label: str) -> Procedure:
        """Impedance Profile (PDN) — Measure power delivery network impedance vs frequency to ensure stability targets."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def inrush_current(label: str) -> Procedure:
        """Inrush Current — Measure initial surge current at power-on to prevent overstress or brownouts."""
        procedure_template = ProcedureBuilder(label)
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure_template.step_call(func, NOARG, "pre-test configuration")
        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def leakage_standby_currrent(label: str) -> Procedure:
        """Leakage/Standby Current — Verify minimal current consumption in idle or low-power states."""

        procedure_template = ProcedureBuilder(label)

        procedure_template.step_call(func, NOARG, "pre-test configuration")

        procedure = procedure_template.generate_procedure()

        return procedure

    @staticmethod
    def dynamic_current_profiling(label: str) -> Procedure:
        """Dynamic Current Profiling — Track current consumption over time under real workloads."""

        procedure_template = ProcedureBuilder(label)

        procedure_template.step_call(func, NOARG, "pre-test configuration")

        procedure = procedure_template.generate_procedure()

        return procedure


class TestBuilderPowerSupply:

    create_session: Callable | None = None
    setup_instruments: Callable | None = None
    setup_dut: Callable | None = None
    start_measure: Callable | None = None
    report: Callable | None = None

    def step_init_test(self, func: Callable):
        self.create_session = func
        return self

    def step_setup_inst(self, func: Callable):
        self.setup_instruments = func
        return self

    def step_dut_setup(self, func: Callable):
        self.setup_dut = func
        return self

    def step_start_measurement(self, func: Callable):
        self.start_measure = func
        return self

    def step_generate_report(self, func: Callable):
        self.report = func
        return self

    def build(self, label: str) -> Procedure:
        """Supply Voltage Accuracy — Verify the DC voltage at the load matches the specified nominal value."""
        template = ProcedureBuilder(label)

        template.step_call(self.create_session, NOARG, "create_session")
        template.step_call(self.setup_instruments, NOARG, "setup_instruments")
        template.step_call(self.setup_dut, NOARG, "setup_dut")
        template.step_call(self.start_measure, NOARG, "start_measure")
        template.step_call(self.report, NOARG, "report")

        procedure = template.generate_procedure()

        return procedure
