Nice use case 👍 `runpy` + threads is a clean way to “launch” a module like it was run with `python -m ...`, but without spawning a new process.

Here’s a **minimal, correct example**, then I’ll point out the gotchas.

---

## Example module to run

**`worker_module.py`**

```python
def main():
    import time
    for i in range(5):
        print(f"[worker] tick {i}")
        time.sleep(1)

if __name__ == "__main__":
    main()
```

---

## Launch that module inside a thread using `runpy`

**`launcher.py`**

```python
import threading
import runpy

def run_module():
    runpy.run_module(
        "worker_module",
        run_name="__main__"   # important!
    )

t = threading.Thread(target=run_module, daemon=True)
t.start()

print("[main] thread started")

t.join()
print("[main] thread finished")
```

### Output

```
[main] thread started
[worker] tick 0
[worker] tick 1
[worker] tick 2
[worker] tick 3
[worker] tick 4
[main] thread finished
```

---

## Why `run_name="__main__"` matters

Without it:

```python
runpy.run_module("worker_module")
```

The `if __name__ == "__main__":` block **will NOT run**.

With it:

```python
runpy.run_module("worker_module", run_name="__main__")
```

The module behaves exactly like:

```
python -m worker_module
```

---

## Passing data into the module (optional pattern)

Since `runpy` executes in a fresh globals dict, you can inject values:

```python
def run_module():
    runpy.run_module(
        "worker_module",
        run_name="__main__",
        init_globals={"CONFIG": {"mode": "test"}}
    )
```

Inside `worker_module.py`:

```python
CONFIG = globals().get("CONFIG", {})
```

---

## Important gotchas (read this 👇)

### 1. **Global state is shared**

* Threads share:

  * `sys.modules`
  * `logging`
  * environment variables
* Two `runpy.run_module()` calls of the same module **can collide**

If you need isolation → **use `multiprocessing`, not threads**

---

### 2. `runpy` is blocking

`runpy.run_module()` runs synchronously **inside the thread**, which is usually what you want.

---

### 3. Exceptions propagate to the thread

Wrap it if needed:

```python
def run_module():
    try:
        runpy.run_module("worker_module", run_name="__main__")
    except Exception as e:
        print("Module crashed:", e)
```

---

## When this pattern is a good idea

✅ Plugin systems
✅ Running CLI-style modules from a GUI
✅ Test harnesses
✅ SCPI simulators / instrument emulators
❌ Strong isolation
❌ Restartable services

---

If you want, next I can show:

* running **multiple modules concurrently**
* capturing `stdout` from the module
* `runpy.run_path()` vs `run_module()`
* why `subprocess` may be safer in some cases

Just say the word 👌
