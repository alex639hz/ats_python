from fastapi import APIRouter

routerGeneral = APIRouter()


@routerGeneral.get("/hello")
def hello_get():
    return "Hello GET"


@routerGeneral.post("/hello")
def hello_post():
    return "Hello POST"
