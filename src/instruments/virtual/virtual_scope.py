import math
import time
from instruments.instrument import Instrument
import logging

from instruments.virtual.virtual_base import VirtualInstrumentBase

logger = logging.getLogger("[virtual_scope]")

DEF_DEMO_SAMPLES_COUNT = 10000
DEF_DEMO_SLEEP_SECONDS = 1


class VirtualScope(VirtualInstrumentBase):
    def __init__(self, instrument: Instrument):
        super().__init__(instrument)
        self.idn = "SCOPE,MODEL-1,1.0"
        self.wave_points = DEF_DEMO_SAMPLES_COUNT
        self.wave_form = "BYTE"
        self.wave_mode = "NORM"
        self.waveform_streaming = b"1"
        self.pder = "+1"
        self._esr_ready_at: float | None = None

    def handle_command(self, cmd: str) -> bytes | None:
        cmd = cmd.strip()
        cmd_u = cmd.upper()
        # ---- Standard Commands ----
        if cmd_u == "*IDN?":
            return (self.idn + "\n").encode()

        elif cmd_u == "*RST":
            self.__init__(self._instrument)
            return b"\n"

        if cmd_u == "*CLS":
            self._esr_ready_at = None
            return b"\n"

        if cmd_u == ":PDER?":
            return b"+1"

        if cmd_u == ":WAVeform:STREAMING?":
            return self.waveform_streaming

        # ---- Waveform Setup ----
        if cmd_u.startswith(":WAV:POIN"):
            self.wave_points = int(cmd.split()[-1])
            return b"\n"

        if cmd_u.startswith(":WAV:FORM"):
            self.wave_form = cmd.split()[-1]
            return b"\n"

        if cmd_u.startswith(":WAV:MODE"):
            self.wave_mode = cmd.split()[-1]
            return b"\n"

        # ---- Waveform Query ----
        if cmd_u == ":WAV:DATA?":
            self._esr_ready_at = time.monotonic()

            logger.info(f"Generating waveform... {DEF_DEMO_SLEEP_SECONDS} seconds")
            time.sleep(DEF_DEMO_SLEEP_SECONDS)
            return self._generate_waveform()

        if cmd_u.startswith(":SIM:DATA? "):
            delay_seconds = int(cmd.split(maxsplit=1)[1])
            self._esr_ready_at = time.monotonic() + delay_seconds
            return b"\n"

        if cmd_u == "*ESR?":
            if self._esr_ready_at is None:
                return b"0\n"

            if time.monotonic() >= self._esr_ready_at:
                return b"1\n"

        raise NotImplementedError(f"Command '{cmd}' not implemented in VirtualScope")

        # ---- Unknown ----
        return b"res\n"

    def _generate_waveform(self) -> bytes:
        """
        Generates sine wave and returns IEEE 488.2 binary block
        """
        samples = []

        for i in range(self.wave_points):
            value = int(127 + 127 * math.sin(2 * math.pi * i / self.wave_points))
            samples.append(value)

        data = bytes(samples)

        # IEEE 488.2 header: #<digits><length>
        length_str = str(len(data))
        header = f"#{len(length_str)}{length_str}".encode()

        return header + data
