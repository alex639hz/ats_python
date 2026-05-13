
---

## Key idea (important)

* **DO NOT** use `query_binary_values()` for large data
  → it buffers everything in memory ❌
* **DO** use:

  * `write()` to send the query
  * `read_bytes()` to manually parse the IEEE-488.2 header
  * then stream the payload in chunks ✅

---

## PyVISA streaming example (binary-safe)

```python
import pyvisa
from typing import BinaryIO


def stream_scpi_binary_to_file(
    inst: pyvisa.resources.MessageBasedResource,
    outfile: BinaryIO,
    chunk_size: int = 64 * 1024,
) -> None:
    """
    Read IEEE-488.2 binary block from a PyVISA instrument
    and stream it directly to a binary file.
    """

    # --- Read '#' ---
    hash_char = inst.read_bytes(1)
    if hash_char != b"#":
        raise ValueError(f"Expected binary block, got {hash_char!r}")

    # --- Read number of digits ---
    n_digits = int(inst.read_bytes(1))
    if n_digits <= 0:
        raise ValueError("Invalid binary block header")

    # --- Read payload length ---
    length_bytes = inst.read_bytes(n_digits)
    total_len = int(length_bytes.decode("ascii"))

    # --- Stream payload ---
    remaining = total_len
    while remaining > 0:
        to_read = min(chunk_size, remaining)
        chunk = inst.read_bytes(to_read)
        outfile.write(chunk)
        remaining -= len(chunk)

    outfile.flush()
```

---

## Example usage

```python
rm = pyvisa.ResourceManager()

inst = rm.open_resource("TCPIP0::192.168.0.50::5025::SOCKET")

# Critical settings for large transfers
inst.timeout = 20_000            # ms
inst.chunk_size = 1024 * 1024    # VISA internal buffer
inst.read_termination = None
inst.write_termination = "\n"

# Request binary data
inst.write(":WAV:DATA?")

with open("waveform.bin", "wb") as f:
    stream_scpi_binary_to_file(inst, f)

inst.close()
rm.close()
```

---

## Why this works reliably

✅ Honors **IEEE-488.2 binary block format**
✅ Streams **GB-scale data safely**
✅ Avoids PyVISA’s hidden buffering
✅ Works over **TCPIP / GPIB / USB**

---

## Very common PyVISA gotchas (read this once)

### ❌ This will break for large data

```python
inst.query_binary_values(":WAV:DATA?")
```

### ❌ This may hang

```python
inst.query(":WAV:DATA?")
```

### ✅ Always do this instead

```python
inst.write(":WAV:DATA?")
stream_scpi_binary_to_file(inst, file)
```

---

## Optional: auto-detect binary vs ASCII

If you want, next we can add:

* `peek` logic to detect `#` vs ASCII response
* SRQ-based reads
* async PyVISA (`pyvisa-py`) integration
* integration into your **instrument I/O worker thread** with queues & futures (which fits your earlier architecture perfectly)

Just tell me where you want to take it 🚀
