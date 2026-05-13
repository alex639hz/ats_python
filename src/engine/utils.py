import os
import threading
import logging
from typing import TYPE_CHECKING, Final
from pathlib import Path
from engine.constants import *
from engine.globals import *

if TYPE_CHECKING:
    from engine.types import *

logger = logging.getLogger("utils")


class Register:
    def __init__(self, address: RegisterAddress, value: int = 0):
        self.address: RegisterAddress = address
        self.value = value

    def write_register(self, value):
        self.value = value

    def read_register(self):
        return self.value

    def write_bit(self, bit_idx, value):
        if value:
            self.value |= 1 << bit_idx
        else:
            self.value &= ~(1 << bit_idx)
        return self.value

    def read_bit(self, bit_idx):
        return (self.value >> bit_idx) & 1


class Utils:

    # TODO create thread launcher helper and update the app
    @staticmethod
    def thread_define(thread_name, thread_function, *args, daemon=True):
        thread = threading.Thread(
            target=thread_function,
            args=(args),
            name=thread_name,
            daemon=daemon,
        )
        return thread

    @staticmethod
    def is_scpi_query(cmd: str) -> bool:
        """Returns True if the command is a SCPI query (i.e., ends with a '?'). This is a simple heuristic and may not cover all cases, but it works for most standard SCPI commands."""
        header = cmd.strip().split(maxsplit=1)[0]
        return header.endswith("?")

    @staticmethod
    def is_scpi_big_query(scpi_cmd: str) -> bool:
        # Common SCPI keywords that usually return binary block data
        _BIG_QUERY_KEYWORDS: Final[tuple[str, ...]] = (
            "WAV",
            "WAVE",
            "DATA",
            "TRAC",
            "TRACE",
            "MMEM",
            "MEM",
            "HCOP",
            "HCOPY",
            "DIG",
            "DIGITIZE",
            "CAPT",
            "IMAGE",
            "IMAG",
            "SCREEN",
            "SYST:SET",
            "SYSTEM:SET",
        )

        """
        Returns True if the SCPI command is likely to return binary block data.
        """
        if not scpi_cmd:
            return False

        scpi_cmd = scpi_cmd.strip().upper()

        # 1. Must be a query
        if "?" not in scpi_cmd:
            return False

        # 2. Match known binary-producing keywords
        for keyword in _BIG_QUERY_KEYWORDS:
            if keyword in scpi_cmd:
                return True

        return False

    @staticmethod
    def q_element_create(cmd="", payload={}):
        return {
            "command": cmd,
            "payload": payload,
        }

    @staticmethod
    def q_element_get_params(q_element):
        return (
            q_element["command"],
            q_element["payload"],
        )

    @staticmethod
    def atomic_file_write_text(path: Path, data: str) -> None:
        """Atomically write text data to a file. This prevents partial writes and ensures that the file is either fully written or not modified at all."""
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(data, encoding="utf-8")
        os.replace(tmp, path)  # atomic

    @staticmethod
    def atomic_file_write_bytes(path: Path, data: bytes) -> None:
        """Atomically write binary data to a file. This prevents partial writes and ensures that the file is either fully written or not modified at all."""
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)

    @staticmethod
    def print_file_as_stream(path: str, chunk_size: int = 32) -> None:
        """Simulate streaming a file by reading it in chunks and printing each byte with its offset. This is useful for debugging or simulating real-time data processing."""
        with open(path, "rb") as f:
            offset = 0
            while chunk := f.read(chunk_size):
                for b in chunk:
                    # print(f"{offset:08d}: {b}")
                    logger.info(f"[STREAM from FILE] {offset:08d}: {b}")

                    offset += 1
