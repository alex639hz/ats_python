from time import time

from engine import procedure
from engine.constants import *
from engine.utils import *
from engine.framework import framework

from typing import Any, Callable, TYPE_CHECKING

from engine.worker import Worker

if TYPE_CHECKING:
    from engine.procedure import Procedure


def null(procedure: Procedure):
    procedure.nextstate_next()
    return "null_operation executed"


def framework_exit(procedure: Procedure):
    procedure.framework.call_shutdown()
    return DEF_OK


def procedure_stop(procedure: Procedure):
    procedure.stop
    return DEF_OK


def function_call(procedure: Procedure):

    step_args = procedure.get_active_step().get_args()
    function: Callable[..., Any] = step_args[STEP_ARG.FUNCTION]
    function_args: dict[str, Any] = step_args[STEP_ARG.ARGS]

    # NOTE set default next state
    procedure.nextstate_next()
    worker_interface: StepInterface = {
        "procedure": procedure,
        "args": function_args,
    }
    res = function(worker_interface)

    return res


def delay_start(procedure: Procedure):
    now = framework.get_time_monotonic()
    procedure.context.attribute_set(DEF_PROC_PARAM.TIMESTAMP, now)
    duration = procedure.get_active_step().get_args().get(STEP_ARG.DURATION_SECONDS)

    return f"sleeping: {duration}"


def delay_check(procedure: Procedure):
    now = framework.get_time_monotonic()
    start_time = procedure.context.attribute_get(DEF_PROC_PARAM.TIMESTAMP)
    delta = now - start_time
    step_args = procedure.get_active_step().get_args()
    target = step_args[STEP_ARG.DURATION_SECONDS]
    should_stay = delta < target

    if should_stay:
        procedure.nextstate_stay()
        return ""

    procedure.nextstate_next()
    return f"sleep completed"


def worker_start(procedure: Procedure):
    step_args = procedure.get_active_step().get_args()
    function = step_args[STEP_ARG.FUNCTION]
    args = step_args[STEP_ARG.ARGS]
    thread_name = step_args[STEP_ARG.TITLE]

    worker = Worker(procedure, function, args, thread_name)
    procedure.context.attribute_set(thread_name, worker)
    worker.start()

    return f"worker start: {thread_name}"


def worker_wait(procedure: Procedure):
    step = procedure.get_active_step()
    worker = procedure.get_worker_from_active_step()
    thread_name = worker.name
    if not worker:
        raise Exception(f"worker not found: {thread_name}")
    elif worker.is_complete():
        procedure.nextstate_next()
        return f"{thread_name} completed"
    else:
        procedure.nextstate_stay()
        return None


step_functions = {
    STEP.NULL: null,
    STEP.FRAMEWORK_EXIT: framework_exit,
    STEP.PROCEDURE_STOP: procedure_stop,
    STEP.FUNC_CALL: function_call,
    STEP.DELAY_START: delay_start,
    STEP.DELAY_WAIT: delay_check,
    STEP.WORKER_START: worker_start,
    STEP.WORKER_WAIT: worker_wait,
}
