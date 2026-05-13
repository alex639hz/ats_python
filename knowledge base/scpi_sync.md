Great question — this is the *missing link* in most SCPI docs.

In the **✅ Professional (SRQ-based)** pattern, **Python never “detects the bit directly”**.
Instead, it detects **SRQ**, *then* reads the registers to find **which bit caused it**.

Here’s the clean mental + code model.

---

## The Correct SRQ Detection Flow (Host Side)

### Instrument side

```scpi
*CLS
*SRE 32      ; Enable OPC → SRQ
:INIT
*OPC         ; Will set ESR.OPC when done
```

### Host side (Python)

1. **Wait for SRQ**
2. **Read STB**
3. **If STB.OPC → read ESR**
4. **Confirm OPC bit**
5. **Continue**

---

## Step-by-Step Python (PyVISA) Example

### 1️⃣ Enable SRQ + OPC

```python
inst.write("*CLS")
inst.write("*SRE 32")   # Enable OPC bit
```

---

### 2️⃣ Start operation

```python
inst.write(":INIT")
inst.write("*OPC")
```

---

### 3️⃣ Wait for SRQ (blocking but safe in worker thread)

```python
inst.wait_for_srq(timeout=5000)
```

✅ This unblocks **only when SRQ line is asserted**

---

### 4️⃣ Read Status Byte (STB)

```python
stb = inst.read_stb()
```

Typical STB bits:

| Bit | Meaning                    |
| --- | -------------------------- |
| 6   | SRQ summary                |
| 5   | ESB (Event Status Summary) |
| 4   | MAV (message available)    |

Check **ESB (bit 5)**:

```python
ESB_MASK = 1 << 5

if stb & ESB_MASK:
    esr = int(inst.query("*ESR?"))
```

---

### 5️⃣ Decode ESR for OPC

```python
OPC_MASK = 1 << 0

if esr & OPC_MASK:
    print("Operation complete")
```

✔ ESR is **latched**
✔ Reading `*ESR?` **clears it**

---

## Minimal SRQ Handler Function

```python
def wait_for_opc(inst, timeout=5000):
    inst.wait_for_srq(timeout=timeout)

    stb = inst.read_stb()
    if not (stb & (1 << 5)):   # ESB
        return False

    esr = int(inst.query("*ESR?"))
    return bool(esr & 1)
```

---

## Why You Must Read Both STB and ESR

| Register | Purpose                         |
| -------- | ------------------------------- |
| STB      | Tells **something happened**    |
| ESR      | Tells **what exactly happened** |

👉 SRQ ≠ OPC
👉 SRQ = “Something worth attention happened”
👉 ESR.OPC = “Your operation finished”

---

## Common SRQ Mistakes (🔥 real-world bugs)

❌ **Reading ESR without checking STB**
→ Missed or misattributed events

❌ **Not calling `*CLS` before arming SRQ**
→ Ghost SRQs from previous sessions

❌ **Using `*OPC?` together with SRQ**
→ Defeats async design

❌ **Waiting for SRQ on GUI thread**
→ UI freeze

---

## Pro Tip for Multi-Instrument Systems

In your **instrument I/O thread**:

* `wait_for_srq()` → event loop
* Push `"OPC_COMPLETE"` into a queue
* Resolve a `Future`

This fits *perfectly* with the design you were already building 👀

---

If you want next:

* Non-blocking SRQ polling
* Handling multiple SRQ causes (errors + OPC)
* VISA event handler (`install_handler`) vs `wait_for_srq`
* A full **threaded SRQ loop** that plays nicely with futures

Just say which one.
