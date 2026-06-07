import threading
from fastapi import FastAPI, Request, HTTPException
from server.routes.routes_general import routerGeneral
from engine.framework import framework

# import server_utils as server_utils

server = FastAPI()


@server.get("/test")
def snapshot():
    threads = threading.enumerate()

    print(f"Active threads: {len(threads)}")
    for t in threads:
        print(f"Name: {t.name}, Alive: {t.is_alive()}, Daemon: {t.daemon}")

    return "test ok"


@server.get("/exit")
def exit():

    framework.call_shutdown()

    return "test ok"


server.include_router(routerGeneral)
