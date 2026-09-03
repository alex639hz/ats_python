"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging

# Note: IN_CODE_IMPORT from engine.server.server_api import server

try:
    import uvicorn
except ModuleNotFoundError:
    uvicorn = None


from engine.utils import Utils

logger = logging.getLogger("main")

HOST = "127.0.0.1"
PORT = 8088


class Server:
    pass

    def __init__(self) -> None:
        self.host = HOST
        self.port = PORT
        self.server_thread = Utils.thread_define("server", self._run_server)

    def _run_server(self):
        if uvicorn is None:
            logger.warning("uvicorn is not installed; API server was not started")
            return

        from engine.server.server_api import server

        uvicorn.run(server, host=HOST, port=PORT, log_level="info")

    def run_server(self):
        self.server_thread.start()
