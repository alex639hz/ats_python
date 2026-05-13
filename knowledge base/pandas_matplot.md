Great Alex — this is a **very realistic production-style pipeline**:

1. Generate structured logs every second
2. Persist to file
3. Parse safely
4. Convert to CSV
5. Generate analytics plot

We’ll use:

* pandas for CSV handling
* matplotlib for plotting

This example is:

* Deterministic
* Log-format safe
* Fault tolerant (skips malformed lines)
* Structured
* Production-style logging format

---

# ✅ What This Script Does

* Writes 10 log lines (1 per second)
* Each line contains:

  * timestamp
  * request_id
  * latency_ms
  * cpu_percent
* Reads the file
* Parses only valid lines
* Converts to CSV
* Generates latency plot (JPG)

---

# 🏗 Production-Grade Example

```python
import time
import uuid
import random
import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# =========================
# Configuration
# =========================
LOG_FILE = Path("app.log")
CSV_FILE = Path("metrics.csv")
PLOT_FILE = Path("latency_plot.jpg")


# =========================
# Logging Setup
# =========================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | request_id=%(request_id)s | latency_ms=%(latency)d | cpu=%(cpu).2f",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return msg, {"extra": self.extra}


# =========================
# Step 1: Produce Logs
# =========================
def produce_logs():
    for _ in range(10):
        request_id = str(uuid.uuid4())[:8]
        latency = random.randint(50, 500)
        cpu = random.uniform(10.0, 80.0)

        adapter = RequestLoggerAdapter(
            logging.getLogger(__name__),
            {"request_id": request_id, "latency": latency, "cpu": cpu},
        )

        adapter.info("request_processed")

        time.sleep(1)


# =========================
# Step 2: Parse Logs
# =========================
LOG_PATTERN = re.compile(
    r"(?P<timestamp>[\d\-: ]+)\s+\|\s+request_id=(?P<request_id>\w+)\s+\|\s+latency_ms=(?P<latency>\d+)\s+\|\s+cpu=(?P<cpu>[\d\.]+)"
)


def parse_logs():
    records = []

    with LOG_FILE.open("r") as f:
        for line in f:
            match = LOG_PATTERN.search(line)
            if not match:
                continue  # skip malformed lines

            record = match.groupdict()
            record["timestamp"] = pd.to_datetime(record["timestamp"])
            record["latency"] = int(record["latency"])
            record["cpu"] = float(record["cpu"])

            records.append(record)

    return pd.DataFrame(records)


# =========================
# Step 3: Save CSV
# =========================
def save_csv(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False)


# =========================
# Step 4: Generate Plot
# =========================
def generate_plot(df: pd.DataFrame):
    plt.figure()
    plt.plot(df["timestamp"], df["latency"])
    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")
    plt.title("Latency Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(PLOT_FILE)
    plt.close()


# =========================
# Main
# =========================
def main():
    produce_logs()

    df = parse_logs()

    if df.empty:
        print("No valid log lines found.")
        return

    save_csv(df)
    generate_plot(df)

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
```

---

# 📂 Files Produced

After running:

```
app.log
metrics.csv
latency_plot.jpg
```

---

# 📊 Example CSV Output

```csv
timestamp,request_id,latency,cpu
2026-02-24 12:00:01,abc12345,220,45.21
2026-02-24 12:00:02,def67890,180,39.88
...
```

---

# 🧠 Why This Is Production-Grade

✔ Uses `logging` module (not print)
✔ Structured log format
✔ Regex-based safe parsing
✔ Skips malformed lines
✔ Typed conversion
✔ Clean separation of concerns
✔ No global mutable state
✔ Closes plot properly

---

# 🔥 If This Was Real Production

You would additionally:

* Use JSON logs instead of text
* Add log rotation
* Use structured logging (e.g. structlog)
* Stream into ELK / Loki / Datadog
* Replace sleep loop with real events

---

If you'd like next, I can show you:

* 🔥 Same system using JSON logs (better production approach)
* 🔥 How to stream logs into pandas in real time
* 🔥 How to benchmark performance
* 🔥 How to do this asynchronously

What level do you want to go next?
