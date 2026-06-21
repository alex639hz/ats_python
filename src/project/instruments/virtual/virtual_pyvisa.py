import time
import threading
import random
from typing import Optional


class FakeVisaInstrument:
    """
    Simulates a PyVISA instrument resource.
    """

    def __init__(
        self,
        resource_name: str,
        write_latency: float = 0.01,
        read_latency: float = 0.02,
        binary_latency_per_mb: float = 0.05,
    ):
        self.resource_name = resource_name
        self.write_latency = write_latency
        self.read_latency = read_latency
        self.binary_latency_per_mb = binary_latency_per_mb

        self._lock = threading.Lock()
        self._last_command: Optional[str] = None
        self._binary_buffer: bytes = b""
        self.timeout = 1.0

    # ---------------------------
    # Core VISA-like API
    # ---------------------------

    def write(self, command: str) -> None:
        """
        Simulates a VISA write (no response expected).
        """
        with self._lock:
            time.sleep(self.write_latency)
            self._last_command = command.strip()

    def read(self) -> str:
        """
        Simulates a VISA read() returning ASCII data.
        """
        with self._lock:
            time.sleep(self.read_latency)

            if self._last_command is None:
                return ""

            # Simple ASCII response simulation
            if self._last_command.endswith("?"):
                return self._simulate_ascii_response(self._last_command)

            return ""

    def query(self, command: str) -> str:
        """
        Simulates write + read (blocking).
        """
        with self._lock:
            self.write(command)
            return self.read()

    def read_raw(self, size: Optional[int] = None) -> bytes:
        """
        Simulates reading raw binary data.
        Compatible with chunked reads.
        """
        with self._lock:
            if not self._binary_buffer:
                return b""

            if size is None or size >= len(self._binary_buffer):
                data = self._binary_buffer
                self._binary_buffer = b""
                return data

            data = self._binary_buffer[:size]
            self._binary_buffer = self._binary_buffer[size:]
            return data

    # ---------------------------
    # Internal simulation logic
    # ---------------------------

    def _simulate_ascii_response(self, command: str) -> str:
        """
        Fake ASCII responses.
        """
        cmd = command.upper()

        if cmd == "*IDN?":
            return "FAKE_INSTRUMENT,MODEL_1234,SN0001,1.0"

        if cmd == "MEAS:VOLT?":
            return f"{random.uniform(0.9, 1.1):.6f}"

        if cmd.startswith("SYST:ERR?"):
            return '0,"No error"'

        return "OK"

    def simulate_binary_response(self, payload_size_bytes: int) -> None:
        """
        Prepares a binary block response for read_raw().
        """
        with self._lock:
            # Simulate transfer latency
            mb = payload_size_bytes / (1024 * 1024)
            time.sleep(mb * self.binary_latency_per_mb)

            payload = bytes(random.getrandbits(8) for _ in range(payload_size_bytes))

            length_str = str(payload_size_bytes)
            header = f"#{len(length_str)}{length_str}".encode()

            self._binary_buffer = header + payload

    # ---------------------------
    # PyVISA-like helpers
    # ---------------------------

    def query_binary_values(
        self,
        command: str,
        datatype: str = "B",
        container=bytes,
    ):
        """
        Simplified stand-in for query_binary_values().
        """
        self.write(command)
        self.simulate_binary_response(1024 * 1024)  # 1 MB default
        raw = self._consume_full_binary_block()
        return container(raw)

    def _consume_full_binary_block(self) -> bytes:
        """
        Reads and strips the SCPI binary header.
        """
        header = self.read_raw(2)
        if not header.startswith(b"#"):
            raise ValueError("Invalid binary block")

        n_digits = int(header[1:2])
        length = int(self.read_raw(n_digits))
        return self.read_raw(length)

    def close(self):
        pass


class ResourceManager:
    """
    Simulates pyvisa.ResourceManager
    """

    def __init__(self):
        self._resources = {}

    def open_resource(self, address: str):
        """
        Returns a new instrument session.
        """
        inst = FakeVisaInstrument(address)
        self._resources[address] = inst
        return inst

    def list_resources(self):
        return tuple(self._resources.keys())
