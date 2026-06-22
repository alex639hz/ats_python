import logging
import json
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from engine.constants import *
from engine.utils import Utils

# =========================
# LOGGING CONSTANTS
# =========================
file_prefix = Utils.timestamp_prefix()
file_prefix = "test"
LOG_FILE = LOG_FOLDER / f"{file_prefix}.log"
DELETE_LOG_ON_STARTUP = True

LOG_LEVEL_CONSOLE = logging.INFO
LOG_LEVEL_FILE = logging.INFO
LOG_MAX_BYTES = 5_000_000
LOG_BACKUP_COUNT = 3

LOG_FORMAT_WITH_TAG = (
    "%(asctime)s [%(levelname)s] " "[%(threadName)s] %(name)s: %(message)s"
)
LOG_FORMAT = "%(asctime)s [%(levelname)s] " "[%(threadName)s]: %(message)s"


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S.%f",
        }
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": "INFO",
        },
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
            "level": "INFO",
        },
    },
}


class NDJsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:

        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        params = getattr(record, "params", None)
        if params != None:
            log_record["params"] = params

        return json.dumps(log_record, separators=(",", ":"))


# =========================
# LOGGING SETUP
# =========================
def setup_logging(q_log):

    LOG_FOLDER.mkdir(parents=True, exist_ok=True)

    if DELETE_LOG_ON_STARTUP and LOG_FILE.exists():
        LOG_FILE.unlink()

    file_handler = RotatingFileHandler(
        filename=str(LOG_FILE),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL_CONSOLE)

    formatter = NDJsonFormatter()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL_CONSOLE)
    console_handler.setFormatter(formatter)
    handlers: list[logging.Handler] = [console_handler]

    if file_handler is isinstance(file_handler, RotatingFileHandler):
        file_handler.setLevel(LOG_LEVEL_FILE)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # --- Queue listener owns real handlers
    listener = QueueListener(
        q_log,
        *handlers,
        respect_handler_level=True,
    )

    # --- Queue handler attached to root logger
    queue_handler = QueueHandler(q_log)
    # queue_handler.setFormatter(formatter)
    logging.root.addHandler(queue_handler)

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    # uvicorn_error_logger.addHandler(queue_handler)
    # uvicorn_access_logger.addHandler(queue_handler)
    # logging.getLogger("uvicorn.access").handlers = [queue_handler]
    # uvicorn_error_logger.handlers = [queue_handler]

    listener.start()
    return listener


class EmptyLogging:
    def stop(self, msg):
        return


class EmptySetupLogging:
    def stop(self):
        return

    def info(self, msg):
        return


class EmptyGetLogger:
    def info(self, msg):
        pass
        return


def empty_setup_logging():
    return EmptySetupLogging()


def empty_get_logger():
    return EmptySetupLogging()
