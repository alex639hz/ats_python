import time
import logging
import uvicorn


from engine.utils import Utils
from api.server import server

logger = logging.getLogger("main")

HOST = "127.0.0.1"
PORT = 8088

from engine.framework import framework


def ui_server():
    uvicorn.run(
        server,
        host=HOST,
        port=PORT,
        log_level="info",
        # log_config=LOG_CONFIG,
    )


Utils.thread_define("ui_server", ui_server).start()

time.sleep(0.1)  # wait for logger to be ready before starting server


logger = logging.getLogger("main")

try:
    if __name__ == "__main__":

        logger.info(" ---------------------- Main start ---------------------- ")
        from project import project

        procedure_1 = project.create_procedure_with_builder("test procedure")
        framework.procedure_append(procedure_1)
        while not framework.event_shutdown.is_set():
            time.sleep(0.1)

except KeyboardInterrupt:
    logger.info(" ---------------------- Main TERMINATED ---------------------- ")

finally:
    framework.call_shutdown()
