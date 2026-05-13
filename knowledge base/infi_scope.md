Your plan is good. I would add one missing point:

**between 2 and 3, always capture the waveform scaling metadata** (`:WAVeform:XINCrement?`, `:WAVeform:XORigin?`, `:WAVeform:YINCrement?`, `:WAVeform:YORigin?`, or `:WAVeform:PREamble?`) so the raw samples can later be converted to time/voltage correctly. On Infiniium, `:WAVeform:DATA?` returns raw sample codes, while `XORigin` is the first point’s X value, `XINCrement` is the spacing between points, `YORigin` is the value represented by code 0, and `YINCrement` is the volts-per-code step. ([Keysight United States][1])

## 1) How large-waveform streaming works on the scope side

For Infiniium, waveform transfer is done with `:WAVeform:DATA?`. With streaming **off**, the response is a normal IEEE-488.2 definite-length block: `# N L <data> <NL>`. With streaming **on**, the guide shows an indefinite block form: `# 0 <data> <NL>`. Keysight explicitly recommends using streaming on for new programs, and says that when streaming is on there is **no limit** on the number of waveform data points returned. By contrast, with streaming off there are practical limits: under `BYTE` format fewer than 1,000,000,000 points, and under `WORD` format fewer than 500,000,000 points. ([Keysight United States][1])

For production code, the safest pattern is:

1. Configure acquisition depth.
2. Trigger and wait for completion.
3. Set waveform source, format, byte order, and `:WAVeform:STReaming ON`.
4. Query `:WAVeform:POINts?` and scaling metadata.
5. Issue `:WAVeform:DATA?`.
6. Stream the payload to disk in chunks instead of building one giant `bytes` object in RAM. ([Keysight United States][1])

A key production detail: with `#0` indefinite blocks, do **not** depend on “read until newline” for the payload. Since you already know the point count and the bytes per sample from the selected waveform format, you can compute the exact payload length and read exactly that many bytes, then read the final terminator separately. That avoids false termination and makes the code simulator-friendly.

---

## 2) Production-grade Python code to get a large waveform

This version is designed to:

* work with a real PyVISA instrument,
* stream directly to a file,
* avoid loading the full waveform into memory,
* support both definite (`#N...`) and streaming (`#0...`) block forms,
* return metadata needed for later decode.

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, BinaryIO
import json


class VisaLike(Protocol):
    def write(self, command: str) -> None: ...
    def read_bytes(self, count: int) -> bytes: ...
    def read(self) -> str: ...
    def query(self, command: str) -> str: ...


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


def _query_str(inst: VisaLike, cmd: str) -> str:
    return inst.query(cmd).strip()


def _query_int(inst: VisaLike, cmd: str) -> int:
    return int(_query_str(inst, cmd))


def _query_float(inst: VisaLike, cmd: str) -> float:
    return float(_query_str(inst, cmd))


def _bytes_per_sample(fmt: str) -> int:
    fmt_upper = fmt.strip().upper()
    if fmt_upper == "BYTE":
        return 1
    if fmt_upper == "WORD":
        return 2
    raise ValueError(f"Unsupported waveform format for raw streaming: {fmt!r}")


def configure_scope_for_large_waveform(
    inst: VisaLike,
    source: str = "CHANnel1",
    points: int = 10_000_000,
    data_format: str = "WORD",
    byte_order: str = "LSBFirst",
) -> None:
    """
    Configure a Keysight Infiniium scope for large waveform transfer.
    """
    inst.write(":SYSTem:HEADer OFF")
    inst.write(":STOP")
    inst.write(":ACQuire:POINts:AUTO OFF")
    inst.write(f":ACQuire:POINts {points}")
    inst.write(f":WAVeform:SOURce {source}")
    inst.write(f":WAVeform:FORMat {data_format}")
    inst.write(f":WAVeform:BYTeorder {byte_order}")
    inst.write(":WAVeform:STReaming ON")


def acquire_single_and_wait(inst: VisaLike) -> None:
    """
    Start a single acquisition and wait for completion.
    """
    inst.write(":SINGle")
    # Simple and portable sync point.
    # Many teams later replace this with a more advanced status/event flow.
    opc = _query_str(inst, "*OPC?")
    if opc != "1":
        raise WaveformStreamError(f"Unexpected *OPC? response: {opc!r}")


def read_waveform_metadata(inst: VisaLike) -> WaveformMetadata:
    source = _query_str(inst, ":WAVeform:SOURce?")
    fmt = _query_str(inst, ":WAVeform:FORMat?")
    byte_order = _query_str(inst, ":WAVeform:BYTeorder?")
    points = _query_int(inst, ":WAVeform:POINts?")
    x_increment = _query_float(inst, ":WAVeform:XINCrement?")
    x_origin = _query_float(inst, ":WAVeform:XORigin?")
    y_increment = _query_float(inst, ":WAVeform:YINCrement?")
    y_origin = _query_float(inst, ":WAVeform:YORigin?")

    return WaveformMetadata(
        source=source,
        points=points,
        format=fmt,
        byte_order=byte_order,
        bytes_per_sample=_bytes_per_sample(fmt),
        x_increment=x_increment,
        x_origin=x_origin,
        y_increment=y_increment,
        y_origin=y_origin,
    )


def _read_exact(inst: VisaLike, total: int, out: BinaryIO | None = None, chunk_size: int = 1 << 20) -> bytes:
    """
    Read exactly `total` bytes.
    If `out` is provided, stream directly into it and return b"".
    """
    remaining = total
    parts: list[bytes] = []

    while remaining > 0:
        take = min(chunk_size, remaining)
        chunk = inst.read_bytes(take)
        if not chunk:
            raise WaveformStreamError(f"Connection closed while reading payload; {remaining} bytes still expected")
        if len(chunk) > remaining:
            raise WaveformStreamError(
                f"Instrument returned too many bytes: got {len(chunk)} with only {remaining} expected"
            )

        if out is not None:
            out.write(chunk)
        else:
            parts.append(chunk)

        remaining -= len(chunk)

    return b"" if out is not None else b"".join(parts)


def _consume_single_terminator(inst: VisaLike) -> None:
    term = inst.read_bytes(1)
    if term not in (b"\n", b"\r"):
        raise WaveformStreamError(f"Expected waveform terminator, got {term!r}")


def stream_waveform_data_to_file(
    inst: VisaLike,
    data_file: Path,
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
    meta = read_waveform_metadata(inst)
    expected_payload_bytes = meta.points * meta.bytes_per_sample

    data_file.parent.mkdir(parents=True, exist_ok=True)

    inst.write(":WAVeform:DATA?")

    hash_char = inst.read_bytes(1)
    if hash_char != b"#":
        raise WaveformStreamError(f"Expected IEEE block '#', got {hash_char!r}")

    block_mode = inst.read_bytes(1)
    if not block_mode:
        raise WaveformStreamError("Missing IEEE block mode byte")

    with data_file.open("wb") as f:
        if block_mode == b"0":
            # Indefinite/streaming form: #0<data><terminator>
            _read_exact(inst, expected_payload_bytes, out=f, chunk_size=chunk_size)
            _consume_single_terminator(inst)
        else:
            if block_mode < b"1" or block_mode > b"9":
                raise WaveformStreamError(f"Invalid IEEE block length-digit byte: {block_mode!r}")

            digits = int(block_mode.decode("ascii"))
            length_ascii = inst.read_bytes(digits)
            if len(length_ascii) != digits or not length_ascii.isdigit():
                raise WaveformStreamError(f"Invalid IEEE block length field: {length_ascii!r}")

            payload_len = int(length_ascii.decode("ascii"))

            if payload_len != expected_payload_bytes:
                raise WaveformStreamError(
                    f"Payload length mismatch: header says {payload_len}, "
                    f"but metadata implies {expected_payload_bytes}"
                )

            _read_exact(inst, payload_len, out=f, chunk_size=chunk_size)
            _consume_single_terminator(inst)

    if metadata_file is not None:
        metadata_file.write_text(json.dumps(meta.__dict__, indent=2), encoding="utf-8")

    return meta
```

### How to use it with a real PyVISA scope

```python
from pathlib import Path
import pyvisa

rm = pyvisa.ResourceManager()
scope = rm.open_resource("TCPIP0::192.168.0.50::inst0::INSTR")

# Optional transport tuning
scope.timeout = 120_000
scope.chunk_size = 1024 * 1024

configure_scope_for_large_waveform(
    scope,
    source="CHANnel1",
    points=20_000_000,
    data_format="WORD",
    byte_order="LSBFirst",
)

acquire_single_and_wait(scope)

meta = stream_waveform_data_to_file(
    scope,
    data_file=Path("waveforms/ch1_raw.bin"),
    metadata_file=Path("waveforms/ch1_raw.json"),
)

print(meta)
```

### Decoding later

For `WORD` data with `LSBFirst`, decode the binary file as signed 16-bit little-endian integers. Then convert to voltage with:

```python
voltage = y_origin + code * y_increment
time = x_origin + index * x_increment
```

That mapping comes directly from the Infiniium waveform scaling queries. ([Keysight United States][1])

---

## 3) Test code with a simulated scope

This simulator is intentionally simple and automation-friendly. It behaves like a VISA resource for the commands your streamer needs.

```python
from __future__ import annotations

from dataclasses import dataclass
import math
import struct


@dataclass
class FakeInfiniiumScope:
    points: int = 2_000_000
    source: str = "CHANnel1"
    waveform_format: str = "WORD"
    byte_order: str = "LSBFirst"
    streaming: bool = True
    x_increment: float = 1e-9
    x_origin: float = 0.0
    y_increment: float = 1e-3
    y_origin: float = 0.0

    def __post_init__(self) -> None:
        self._pending_read = bytearray()
        self._acquired = False

    def write(self, command: str) -> None:
        cmd = command.strip()
        upper = cmd.upper()

        if upper == ":SYSTEM:HEADER OFF":
            return
        if upper == ":STOP":
            return
        if upper == ":SINGLE":
            self._acquired = True
            return
        if upper == ":WAVEFORM:STREAMING ON":
            self.streaming = True
            return
        if upper == ":WAVEFORM:STREAMING OFF":
            self.streaming = False
            return

        if upper.startswith(":ACQUIRE:POINTS:AUTO "):
            return

        if upper.startswith(":ACQUIRE:POINTS "):
            self.points = int(cmd.split()[-1])
            return

        if upper.startswith(":WAVEFORM:SOURCE "):
            self.source = cmd.split()[-1]
            return

        if upper.startswith(":WAVEFORM:FORMAT "):
            self.waveform_format = cmd.split()[-1].upper()
            return

        if upper.startswith(":WAVEFORM:BYTEORDER "):
            self.byte_order = cmd.split()[-1]
            return

        if upper == ":WAVEFORM:DATA?":
            payload = self._build_waveform_payload()
            if self.streaming:
                # #0<data>\n
                self._pending_read = bytearray(b"#0" + payload + b"\n")
            else:
                length_ascii = str(len(payload)).encode("ascii")
                # #Nlen<data>\n
                self._pending_read = bytearray(
                    b"#" + str(len(length_ascii)).encode("ascii") + length_ascii + payload + b"\n"
                )
            return

        raise NotImplementedError(f"Unsupported write command: {command!r}")

    def read_bytes(self, count: int) -> bytes:
        if count <= 0:
            return b""

        if not self._pending_read:
            return b""

        n = min(count, len(self._pending_read))
        out = bytes(self._pending_read[:n])
        del self._pending_read[:n]
        return out

    def read(self) -> str:
        if not self._pending_read:
            return ""

        nl_index = self._pending_read.find(b"\n")
        if nl_index == -1:
            out = bytes(self._pending_read)
            self._pending_read.clear()
            return out.decode("ascii")

        out = bytes(self._pending_read[:nl_index + 1])
        del self._pending_read[:nl_index + 1]
        return out.decode("ascii")

    def query(self, command: str) -> str:
        cmd = command.strip().upper()

        if cmd == "*OPC?":
            return "1\n"
        if cmd == ":WAVEFORM:SOURCE?":
            return f"{self.source}\n"
        if cmd == ":WAVEFORM:FORMAT?":
            return f"{self.waveform_format}\n"
        if cmd == ":WAVEFORM:BYTEORDER?":
            return f"{self.byte_order}\n"
        if cmd == ":WAVEFORM:STREAMING?":
            return f"{1 if self.streaming else 0}\n"
        if cmd == ":WAVEFORM:POINTS?":
            return f"{self.points}\n"
        if cmd == ":WAVEFORM:XINCREMENT?":
            return f"{self.x_increment}\n"
        if cmd == ":WAVEFORM:XORIGIN?":
            return f"{self.x_origin}\n"
        if cmd == ":WAVEFORM:YINCREMENT?":
            return f"{self.y_increment}\n"
        if cmd == ":WAVEFORM:YORIGIN?":
            return f"{self.y_origin}\n"

        raise NotImplementedError(f"Unsupported query command: {command!r}")

    def _build_waveform_payload(self) -> bytes:
        """
        Build a deterministic sine waveform.
        WORD => signed int16
        BYTE => signed int8
        """
        if self.waveform_format == "WORD":
            samples = []
            amplitude = 20_000
            for i in range(self.points):
                angle = 2.0 * math.pi * (i / 2000.0)
                code = int(amplitude * math.sin(angle))
                samples.append(code)

            endian = "<" if self.byte_order.upper() == "LSBFIRST" else ">"
            return struct.pack(f"{endian}{len(samples)}h", *samples)

        if self.waveform_format == "BYTE":
            samples = []
            amplitude = 100
            for i in range(self.points):
                angle = 2.0 * math.pi * (i / 500.0)
                code = int(amplitude * math.sin(angle))
                samples.append(code)

            return struct.pack(f"{len(samples)}b", *samples)

        raise ValueError(f"Unsupported waveform format: {self.waveform_format}")
```

### End-to-end test

```python
from pathlib import Path

def test_large_waveform_streaming(tmp_path: Path) -> None:
    scope = FakeInfiniiumScope(points=3_000_000)

    configure_scope_for_large_waveform(
        scope,
        source="CHANnel1",
        points=3_000_000,
        data_format="WORD",
        byte_order="LSBFirst",
    )

    acquire_single_and_wait(scope)

    raw_path = tmp_path / "ch1_raw.bin"
    meta_path = tmp_path / "ch1_raw.json"

    meta = stream_waveform_data_to_file(
        scope,
        data_file=raw_path,
        metadata_file=meta_path,
        chunk_size=256 * 1024,
    )

    assert meta.points == 3_000_000
    assert meta.format == "WORD"
    assert meta.bytes_per_sample == 2
    assert raw_path.exists()
    assert raw_path.stat().st_size == 3_000_000 * 2
    assert meta_path.exists()
```

### Small runnable demo

```python
from pathlib import Path

def main() -> None:
    scope = FakeInfiniiumScope(points=1_000_000)

    configure_scope_for_large_waveform(
        scope,
        source="CHANnel1",
        points=1_000_000,
        data_format="WORD",
        byte_order="LSBFirst",
    )

    acquire_single_and_wait(scope)

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    meta = stream_waveform_data_to_file(
        scope,
        data_file=out_dir / "waveform.bin",
        metadata_file=out_dir / "waveform.json",
    )

    print("Done")
    print(meta)
    print("Binary size:", (out_dir / "waveform.bin").stat().st_size)

if __name__ == "__main__":
    main()
```

## My recommendation on architecture

For your automation framework, split it into 3 layers:

1. **SCPI configuration layer**
   sends commands like `:ACQuire:POINts`, `:WAVeform:FORMat`, `:WAVeform:STReaming ON`.

2. **binary transport layer**
   only knows how to read the `#...` block safely and stream it to disk.

3. **decode layer**
   converts raw file + metadata into engineering values.

That separation makes the simulator much easier, because your fake instrument only needs to emulate a narrow command set and a binary block producer.

The one thing I would change from your original plan is this: **do not make the first version parse the waveform while downloading it**. First get a rock-solid raw streamer. Then add a separate decoder test over the saved file. That keeps memory use low and makes failures much easier to debug.

I can next give you a version wrapped as a single reusable class, or a pytest suite with real assertions for both `#0` and `#N` modes.

[1]: https://www.keysight.com/us/en/assets/9018-07141/programming-guides/9018-07141.pdf "Programmer's Guide for Infiniium Oscilloscopes (PDF)"
