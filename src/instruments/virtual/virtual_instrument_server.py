import socket
import threading
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instruments.instrument import Instrument


HOST = "127.0.0.1"
DEF_BYTES_TO_READ = 1024
DEF_SHOULD_LOG = False

logger = logging.getLogger("[virtual]")


def logger_cmd(log_msg: str) -> None:
    if DEF_SHOULD_LOG:
        logger.info(log_msg)


def client_handler(conn: socket.socket, addr, virtual_instrument) -> None:
    buffer = b""

    try:
        logger_cmd(f"{virtual_instrument._label}\tCONNECT:\t{addr}")

        while True:
            chunk = conn.recv(DEF_BYTES_TO_READ)
            if not chunk:
                break

            buffer += chunk

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                cmd = line.decode(errors="ignore").strip()
                logger_cmd(f"{virtual_instrument._label}\tRX:\t{cmd}")

                response = virtual_instrument.handle_command(cmd)
                if response is not None:
                    if isinstance(response, str):
                        response = response.encode()

                    conn.sendall(response)
                    logger_cmd(f"{virtual_instrument._label}\tTX:\t{response!r}")

    except Exception as e:
        logger.exception("%s\tERROR:\t%s", virtual_instrument._label, e)

    finally:
        conn.close()
        logger_cmd(f"{virtual_instrument._label}\tDISCONNECT:\t{addr}")


def start_server(virtual_instrument) -> None:
    port = virtual_instrument._instrument._virtual_port
    label = virtual_instrument._instrument._label

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port))
        s.listen(5)

        logger.info("%s v_server listening on %s:%s", label, HOST, port)

        while True:
            conn, addr = s.accept()
            threading.Thread(
                name=f"vInstrThread-{addr[0]}:{addr[1]}",
                target=client_handler,
                args=(conn, addr, virtual_instrument),
                daemon=True,
            ).start()
