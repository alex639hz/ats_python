"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import threading
from fastapi import FastAPI, Request, HTTPException
from engine.server.routes.routes_general import routerGeneral
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

# Station Management:


@server.post("/register")
def register(server_id: str):
    """register Set the server ID in the framework context."""
    if not server_id or not isinstance(server_id, str):
        raise HTTPException(
            status_code=400, detail="server_id must be a non-empty string"
        )

    try:
        framework.context.attribute_set("server_id", server_id)
        return {"status": "success", "server_id": server_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set server_id: {str(e)}"
        )


# TODO
@server.get("/config")
def get_config(server_id):
    """register Set the server ID in the framework context."""
    if not server_id or not isinstance(server_id, str):
        raise HTTPException(
            status_code=400, detail="server_id must be a non-empty string"
        )

    try:
        framework.context.attribute_set("server_id", server_id)
        return {"status": "success", "server_id": server_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set server_id: {str(e)}"
        )


# TODO
@server.get("/proc/{id}")
def get_procedure(id):
    if not id or not isinstance(id, str):
        raise HTTPException(
            status_code=400, detail="id must be a non-empty numeric string"
        )

    try:
        procedure_id = int(id)
        max = len(framework._procedure_list)
        if procedure_id < 0 or procedure_id > max:
            raise ValueError(f"id must be 0..{max}")
        procedure = framework._procedure_list[procedure_id]
        return {"status": "success", "procedure": procedure}
    except ValueError:
        raise HTTPException(
            status_code=400, detail="id must be a valid non-negative integer"
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Procedure {id} not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get procedure: {str(e)}"
        )
