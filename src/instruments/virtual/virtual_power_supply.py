from instruments.instrument import Instrument
from instruments.virtual.virtual_base import VirtualInstrumentBase


class VirtualPowerSupply(VirtualInstrumentBase):

    def __init__(self, instrument: Instrument):
        super().__init__(instrument)
        self.voltage = 5.0
        self.current_limit = 1.0
        self.output = False

    def handle_command(self, cmd: str) -> bytes | None:
        cmd = cmd.strip().upper()

        if cmd == "*IDN?":
            return b"V-PS 1.0\n"

        if cmd == "*TST?":
            return b"Test OK\n"

        # Voltage
        if cmd.startswith("VOLT "):
            self.voltage = float(cmd.split()[1])
            return None

        if cmd == "VOLT?":
            return f"{self.voltage}\n".encode()

        # Current
        if cmd.startswith("CURR "):
            self.current_limit = float(cmd.split()[1])
            return None

        if cmd == "CURR?":
            return f"{self.current_limit}\n".encode()

        # Output
        if cmd == "OUTP ON":
            self.output = True
            return None

        if cmd == "OUTP OFF":
            self.output = False
            return None

        if cmd == "OUTP?":
            return b"1\n" if self.output else b"0\n"

        # Measurements
        if cmd == "MEAS:VOLT?":
            return f"{self.voltage if self.output else 0.0}\n".encode()

        if cmd == "MEAS:CURR?":
            measured = min(self.current_limit, self.voltage / 10)
            return f"{measured if self.output else 0.0}\n".encode()

        return b"ERROR\n"
