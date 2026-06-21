# import time
# import logging
import uvicorn


from engine.utils import Utils

# logger = logging.getLogger("main")

HOST = "127.0.0.1"
PORT = 8088


def _run_server():
    from engine.server.server_api import server

    uvicorn.run(server, host=HOST, port=PORT, log_level="info")


def run_server():
    Utils.thread_define("server", _run_server).start()
