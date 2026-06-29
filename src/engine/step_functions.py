from time import time

from engine import procedure
from engine.constants import *
from engine.utils import *
from engine.framework import framework

from typing import Callable, TYPE_CHECKING

from engine.worker import Worker

if TYPE_CHECKING:
    from engine.procedure import Procedure


def null(procedure: Procedure):
    procedure.nextstate_next()
    return "null_operation executed"


def exit(procedure: Procedure):
    procedure.framework.call_shutdown()
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


#     def loop(procedure):
#         Engine.post_step_action_next(procedure)

#     def for_loop(procedure):
#         step_args = Utils.procedure_get_active_step_args(procedure)
#         header = Utils.procedure_get_header(procedure)

#         if not header.get(DEF_HEAD_KEY.FOR_LOOP_INDEX):
#             initial_index = 1
#             header[DEF_HEAD_KEY.FOR_LOOP_INDEX] = initial_index

#         index = header[DEF_HEAD_KEY.FOR_LOOP_INDEX]
#         limit = step_args[DEF_STEP_ARG.FOR_LOOP_LIMIT]

#         if index < limit:
#             step_to_return = step_args[DEF_STEP_ARG.STEP_TO_RETURN]
#             header[DEF_HEAD_KEY.FOR_LOOP_INDEX] = index + 1
#             Engine.post_step_action_jump(procedure, step_to_return)
#             log_msg = f"jump to {step_to_return}"
#             return log_msg

#         Engine.post_step_action_next(procedure)
#         log_msg = f"for loop completed {index} iterations"
#         return log_msg

#     def procedure_stop(procedure):
#         Utils.procedure_deactivate(procedure)
#         Engine.post_step_action_next(procedure)

#     def procedure_start(procedure):
#         Utils.procedure_activate(procedure)
#         Engine.post_step_action_next(procedure)

#     def engine_stop(procedure):
#         global_context.flag_set(global_context.DefFlagKeys.IS_RUNNING, False)
#         Engine.post_step_action_next(procedure)

#     def exit(procedure):
#         sys.exit(0)

#     def scpi_request(procedure):
#         step = Utils.procedure_get_active_step(procedure)

#         step_label = step[DEF_STEP_KEY.LABEL]
#         step_args = step[DEF_STEP_KEY.ARGS]

#         scpi_instrument = step_args[DEF_STEP_ARG.SCPI_INSTRUMENT]
#         scpi_command = step_args[DEF_STEP_ARG.SCPI_CMD].value

#         # instrument = self.instrument_by_label.get(scpi_instrument)
#         instrument = self.instruments_repo.get_by_label(scpi_instrument)

#         if not instrument:
#             msg = f"instrument {scpi_instrument} not in repository"
#             Engine.post_step_action_stop_process_with_error(procedure, {"msg": msg})
#             return msg

#         res = instrument.api_std_request(scpi_command)

#         if not res:
#             msg = f"instrument {scpi_instrument} not in repository"
#             Engine.post_step_action_repeat_with_warning(procedure, {"msg": msg})
#             return msg

#         Engine.post_step_action_next(procedure)
#         return f"{scpi_instrument} : {scpi_command} -> {res}"


step_functions = {
    # DEF_STEP_OP.LOOP_FOREVER: loop,
    # DEF_STEP_OP.FOR_LOOP: for_loop,
    # DEF_STEP_OP.SCRIPT_RUN: script_run,
    # DEF_STEP_OP.PROCEDURE_START: procedure_start,
    # DEF_STEP_OP.PROCEDURE_STOP: procedure_stop,
    # DEF_STEP_OP.ENGINE_STOP: engine_stop,
    # DEF_STEP_OP.EXIT: exit,
    # DEF_STEP_OP.SCPI_REQUEST: scpi_request,
    STEP.NULL: null,
    STEP.EXIT: exit,
    STEP.FUNCTION_CALL: function_call,
    STEP.DELAY_START: delay_start,
    STEP.DELAY_WAIT: delay_check,
    STEP.WORKER_START: worker_start,
    STEP.WORKER_WAIT: worker_wait,
    # DEF_STEP_OP.INSTRUMENT_INIT: create_step_instrument_init,
    # DEF_STEP_OP.PRINT: _print,
    # DEF_STEP_OP.QUEUE_CREATE: _queue_create,
}
