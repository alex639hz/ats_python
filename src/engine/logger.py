import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path

# =========================
# LOGGING CONSTANTS
# =========================
LOG_DIR = Path(r"C:\ATS\logs")
LOG_FILE = LOG_DIR / "app.log"
DELETE_LOG_ON_STARTUP = True

LOG_LEVEL = logging.INFO
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


# =========================
# LOGGING SETUP
# =========================
def setup_logging(q_log):
    # --- Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # --- Delete log file on startup (BEFORE handlers)
    if DELETE_LOG_ON_STARTUP and LOG_FILE.exists():
        LOG_FILE.unlink()

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(LOG_FORMAT)

    # --- Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    #
    # --- File handler (absolute path)
    file_handler = RotatingFileHandler(
        filename=str(LOG_FILE),  # logging expects str
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    # --- Queue listener owns real handlers
    listener = QueueListener(
        q_log,
        console_handler,
        file_handler,
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
