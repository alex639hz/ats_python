from dataclasses import dataclass
from pathlib import Path
import time
import logging
from typing import BinaryIO
import numpy as np

# from engine.constants import DEF_STEP_OP
# from engine.utils import Utils

# from engine.instruments.instrument import Instrument
from project.instruments.instrument import Instrument
from project.instruments.instrument_repo import repository

logger = logging.getLogger("[scope]")


OUTPUT_ON = True
OUTPUT_OFF = False


@dataclass(frozen=True)
class WaveformMetadata:
    source: str
    points: int
    format: str
    byte_order: str
    bytes_per_sample: int
    x_increment: float
    x_origin: float
    y_increment: float
    y_origin: float


class WaveformStreamError(RuntimeError):
    pass


class Scope(Instrument):
    DEF_CHANNEL_STATE_OFF = 0
    DEF_CHANNEL_STATE_ON = 1
    _model = "N6700C"
    _channel = 0
    _total_channels = 1
    _voltage = 0

    def setup(self):
        pass

    def __init__(self, instrument):
        super().__init__(instrument)

    def get_waveform_auto(self, callback):

        points = 0

        self.request(":WAV:DATA?", callback)

    def get_reg_pder(self):
        res = self.request(":PDER?")
        return int(res)

    def get_waveform_single(self):
        self.request(":SINGle")

    def get_waveform_points(self):
        self.request(":WAVeform:POINts?")

    def sync_with_opc(self, scpi: str, timeout_seconds=60):
        start_time = time.monotonic()
        end_timeout = start_time + timeout_seconds

        self.std_cls()
        esr = self.std_esr()
        self.request(scpi)
        self.request("*OPC")
        while (int(esr) & 1) == 0 and time.monotonic() < end_timeout:
            time.sleep(0.5)
            esr = self.std_esr()
            logger.info(f"waiting for OPC... ESR={esr}")

        total_time = time.monotonic() - start_time
        status_msg = "timeout" if time.monotonic() > end_timeout else ""
        logger.info(f"sync_with_opc() {status_msg} total time {total_time:.1f} seconds")

    @staticmethod
    def bytes_per_sample(fmt: str) -> int:
        #     fmt_upper = fmt.strip().upper()
        #     if fmt_upper == "BYTE":
        #         return 1
        #     if fmt_upper == "WORD":
        #         return 2
        #     raise ValueError(f"Unsupported waveform format for raw streaming: {fmt!r}")
        return 2

    def get_waveform_single_or_timeout(self, timeout_seconds=60):
        """call SINGLE and wait for PDER register to be set or timeout"""
        start_time = time.monotonic()
        end_timeout = start_time + timeout_seconds

        self.std_cls()
        pder_register = self.get_reg_pder()

        if pder_register:
            raise Exception("PDER register is not cleared before SINGLE measurment")

        self.get_waveform_single()

        while not pder_register and time.monotonic() < end_timeout:
            pder_register = self.get_reg_pder()

        total_time = time.monotonic() - start_time
        logger.info(f"get single waveform total time {total_time:.1f} seconds")

        if not pder_register:
            raise Exception(f"Timeout while getting single waveform")

    def execute_and_wait_pder(self, func, timeout_seconds=60):
        """call 'func' function and wait for PDER register to be set or timeout."""

        start_time = time.monotonic()
        end_timeout = start_time + timeout_seconds

        self.std_cls()
        pder_register = self.get_reg_pder()

        if pder_register:
            raise Exception("PDER register is not cleared before execution")

        res = func()

        while not pder_register and time.monotonic() < end_timeout:
            pder_register = self.get_reg_pder()
            time.sleep(0.5)

        total_time = time.monotonic() - start_time
        status_msg = "timeout" if time.monotonic() > end_timeout else ""
        logger.info(
            f"execute_and_wait_pder() {status_msg} total time {total_time:.1f} seconds"
        )

        if not pder_register:
            raise Exception(f"Timeout while getting single waveform")

        return res

    def set_waveform_metadata(
        self,
        source: str,
        format: str,
        byte_order: str,
        points: int,
        x_increment: float,
        x_origin: float,
        y_increment: float,
        y_origin: float,
    ):
        pass

    def read_waveform_metadata(self) -> WaveformMetadata:
        source = self.request_str(":WAVeform:SOURce?")
        format = self.request_str(":WAVeform:FORMat?")
        byte_order = self.request_str(":WAVeform:BYTeorder?")
        points = self.request_int(":WAVeform:POINts?")
        x_increment = self.request_float(":WAVeform:XINCrement?")
        x_origin = self.request_float(":WAVeform:XORigin?")
        y_increment = self.request_float(":WAVeform:YINCrement?")
        y_origin = self.request_float(":WAVeform:YORigin?")

        return WaveformMetadata(
            source=source,
            points=points,
            format=format,
            byte_order=byte_order,
            bytes_per_sample=self.bytes_per_sample(format),
            x_increment=x_increment,
            x_origin=x_origin,
            y_increment=y_increment,
            y_origin=y_origin,
        )

    def _read_exact(
        self, total: int, out: BinaryIO | None = None, chunk_size: int = 1 << 20
    ) -> bytes:
        """
        Read exactly `total` bytes.
        If `out` is provided, stream directly into it and return b"".
        """
        remaining = total
        parts: list[bytes] = []

        while remaining > 0:

            bytes_count = min(chunk_size, remaining)

            start_time = time.monotonic()
            chunk = self.connection.read_bytes(bytes_count)
            end_time = time.monotonic()

            if not chunk:
                raise WaveformStreamError(
                    f"Connection closed while reading payload; {remaining} bytes still expected"
                )

            if len(chunk) > remaining:
                raise WaveformStreamError(
                    f"Instrument returned too many bytes: got {len(chunk)} with only {remaining} expected"
                )

            if out is not None:
                out.write(chunk)
            else:
                parts.append(chunk)

            remaining -= len(chunk)

            # logger.info(f"Start streaming {total} bytes")
            logger.info(
                f"read chunk of {bytes_count:_} bytes, duration {(end_time - start_time):.2f} seconds, remaining: {remaining:_}"
            )

        return b"" if out is not None else b"".join(parts)

    def _consume_single_terminator(self) -> None:
        term = self.connection.read_bytes(1)
        if term not in (b"\n", b"\r"):
            raise WaveformStreamError(f"Expected waveform terminator, got {term!r}")

    def stream_waveform_data_to_file(
        self,
        bin_filepath: Path,
        metadata_file: Path | None = None,
        chunk_size: int = 1 << 20,
    ) -> WaveformMetadata:
        """
        Stream waveform payload from :WAVeform:DATA? directly to `data_file`.

        Supports both:
        - definite IEEE block: #<N><len><payload><NL>
        - streaming/indefinite block: #0<payload><NL>

        For '#0', the payload length is derived from waveform metadata
        (points * bytes_per_sample), which is robust and simulator-friendly.
        """

        meta = self.read_waveform_metadata()
        expected_payload_size = meta.points * meta.bytes_per_sample

        logger.info(f"Start streaming {expected_payload_size:_} bytes")

        start_record_time = time.monotonic()

        bin_filepath.parent.mkdir(parents=True, exist_ok=True)

        self.connection.write(":WAVeform:DATA?")

        hash_char = self.connection.read_bytes(1)
        if hash_char != b"#":
            raise WaveformStreamError(f"Expected IEEE block '#', got {hash_char!r}")

        block_mode = self.connection.read_bytes(1)
        if not block_mode:
            raise WaveformStreamError("Missing IEEE block mode byte")

        with bin_filepath.open("wb") as f:
            if block_mode == b"0":
                # Indefinite/streaming form: #0<data><terminator>
                self._read_exact(expected_payload_size, out=f, chunk_size=chunk_size)
                self._consume_single_terminator()
            else:
                if block_mode < b"1" or block_mode > b"9":
                    raise WaveformStreamError(
                        f"Invalid IEEE block length-digit byte: {block_mode!r}"
                    )

                digits = int(block_mode.decode("ascii"))
                length_ascii = self.connection.read_bytes(digits)

                if len(length_ascii) != digits or not length_ascii.isdigit():
                    raise WaveformStreamError(
                        f"Invalid IEEE block length field: {length_ascii!r}"
                    )

                payload_len = int(length_ascii.decode("ascii"))

                if payload_len != expected_payload_size:
                    raise WaveformStreamError(
                        f"Payload length mismatch: header says {payload_len}, "
                        f"but metadata implies {expected_payload_size}"
                    )

                self._read_exact(payload_len, out=f, chunk_size=chunk_size)
                self._consume_single_terminator()

        end_record_time = time.monotonic()
        logger.info(
            f"Streaming total time {int(end_record_time-start_record_time)} seconds"
        )

        CONVERT_BIN_TO_TXT = False
        if CONVERT_BIN_TO_TXT:
            logger.info(f"Start converting binary to ascii {str(bin_filepath)}")
            start_convert_time = time.monotonic()

            self.convert_bin_to_float_txt(
                bin_filepath,
                bin_filepath.with_suffix(".txt"),
                meta.y_increment,
                meta.y_origin,
                meta.x_increment,
                meta.x_origin,
                meta.byte_order,
            )

            end_convert_time = time.monotonic()

            logger.info(
                f"Convert total time {int(end_convert_time - start_convert_time)} seconds"
            )

        if metadata_file is not None:
            # metadata_file.write_text(json.dumps(meta.__dict__, indent=2), encoding="utf-8")
            pass

        return meta
        # pass

    @staticmethod
    def convert_bin_to_float_txt(
        bin_path: Path,
        txt_path: Path,
        y_increment: float,
        y_origin: float,
        x_increment: float,
        x_origin: float = 0.0,
        byte_order: str = "LSBF",
        chunk_size: int = 1 << 20,
    ) -> None:
        """
        Stream WORD waveform binary file and convert it to a text file
        with two columns:
            timestamp,value

        Parameters:
            bin_path: input binary file containing raw WORD waveform data
            txt_path: output text file
            y_increment: volts per LSB
            y_origin: voltage offset
            x_increment: time step between consecutive samples
            x_origin: timestamp of the first sample
            byte_order: "LSBFirst" or "MSBFirst"
            chunk_size: bytes per read, must be even for WORD data
        """
        if chunk_size % 2 != 0:
            raise ValueError("chunk_size must be even for WORD data")

        if byte_order.upper() in ("LSBFIRST", "LSBF"):
            dtype = "<i2"  # little-endian int16
        elif byte_order.upper() in ("MSBFIRST", "MSBF"):
            dtype = ">i2"  # big-endian int16
        else:
            raise ValueError(f"Invalid byte_order: {byte_order}")

        leftover = b""
        sample_index = 0

        with bin_path.open("rb") as bin_file, txt_path.open(
            "w", encoding="utf-8"
        ) as txt_file:
            txt_file.write("timestamp,value\n")

            while True:
                chunk = bin_file.read(chunk_size)
                if not chunk:
                    break

                chunk = leftover + chunk

                if len(chunk) % 2 != 0:
                    leftover = chunk[-1:]
                    chunk = chunk[:-1]
                else:
                    leftover = b""

                if not chunk:
                    continue

                codes = np.frombuffer(chunk, dtype=dtype)
                values = y_origin + (codes.astype(np.float64) * y_increment)

                count = len(values)
                timestamps = x_origin + (
                    np.arange(sample_index, sample_index + count, dtype=np.float64)
                    * x_increment
                )

                start_time = time.monotonic()

                for ts, val in zip(timestamps, values):
                    txt_file.write(f"{ts:.10f},{val:.9f}\n")

                end_time = time.monotonic()

                logger.info(
                    f"converting to *.txt. chunk size: {len(chunk)}, duration {(end_time - start_time):.2f} seconds"
                )

                sample_index += count

            if leftover:
                raise ValueError("Corrupted file: odd number of bytes in WORD data")

    def measure_volt_rms(self):
        volt_rms: float = self.request_float(":MEAS:VRMS? CHAN1")
        return volt_rms
