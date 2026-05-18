from time import time

from engine import procedure
from engine.constants import *
from engine.utils import *

from typing import Callable, TYPE_CHECKING

from engine.worker import Worker

if TYPE_CHECKING:
    from engine.procedure import Procedure


def null(procedure: Procedure):
    procedure.nextstate_next()
    return "null_operation executed"


def exit(procedure: Procedure):
    procedure._framework.call_shutdown()
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
    now = time.monotonic()
    procedure.set_variable(DEF_PROC_PARAM.TIMESTAMP, now)
    return DEF_OK


def delay_check(procedure: Procedure):
    now = time.monotonic()
    start_time = procedure.get_variable(DEF_PROC_PARAM.TIMESTAMP)
    delta = now - start_time
    step_args = procedure.get_active_step().get_args()
    target = step_args[STEP_ARG.DURATION_SECONDS]
    should_stay = delta < target

    if should_stay:
        procedure.nextstate_stay()
        return ""

    procedure.nextstate_next()
    return f"sleep %0.1f seconds completed" % delta


def worker_start(procedure: Procedure):
    step_args = procedure.get_active_step().get_args()
    function = step_args[STEP_ARG.FUNCTION]
    args = step_args[STEP_ARG.ARGS]
    thread_name = step_args[STEP_ARG.TITLE]

    w1 = Worker(procedure, function, args, thread_name)
    procedure.session_var_set(thread_name, w1)
    w1.start()
    # w1.wait()
    # procedure.nextstate_next()

    pass


def worker_check(procedure: Procedure):
    # step_args = procedure.get_active_step().get_args()
    # thread_name = step_args[DEF_STEP_ARG.TITLE]
    # worker: Worker | None = procedure.session_var_get(thread_name)

    worker = procedure.get_worker_from_active_step()
    thread_name = worker.name
    if not worker:
        raise Exception(f"worker '{thread_name}' not found in session")
    elif worker.is_complete():
        procedure.nextstate_next()
        return f"worker '{thread_name}' completed"
    else:
        procedure.nextstate_stay()
        return None  # f"worker '{thread_name}' is running"


#     @staticmethod
#     def time_load(procedure: Procedure):
#         procedure._params[DEF_HEAD_KEY.TIMESTAMP_SECONDS] = time.monotonic()

#         # -------------------
#         header = Utils.procedure_get_header(procedure)
#         step_args = Utils.procedure_get_active_step_args(procedure)
#         header[DEF_HEAD_KEY.TIMESTAMP_SECONDS] = time.monotonic()

#         Engine.post_step_action_next(procedure)
#         log_msg = f"sleep: {step_args[DEF_STEP_ARG.DURATION_SECONDS]} seconds"

#         return log_msg

#     def time_check(procedure):
#         now = time.monotonic()
#         # header[HeadKeys.TIMESTAMP_SECONDS] = now_ns
#         header = Utils.procedure_get_header(procedure)
#         step = Utils.procedure_get_active_step(procedure)
#         start = header[DEF_HEAD_KEY.TIMESTAMP_SECONDS]
#         delta = now - start
#         target = step[DEF_STEP_KEY.ARGS][DEF_STEP_ARG.DURATION_SECONDS]
#         should_stay = delta < target
#         header[DEF_HEAD_KEY.TIMER_ELAPSED_SECONDS] = delta

#         if should_stay:
#             Engine.post_step_action_stay(procedure)
#             log_msg = None
#         else:
#             Engine.post_step_action_next(procedure)
#             log_msg = None and f"sleep %0.2f seconds completed" % delta

#         return log_msg

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

#     def script_run(procedure):
#         step = Utils.procedure_get_active_step(procedure)
#         step_args = step[DEF_STEP_KEY.ARGS]
#         script_path = step_args[DEF_STEP_ARG.PATH]
#         use_join = step_args[DEF_STEP_ARG.WAIT_THREAD]
#         queue_label = step_args.get(DEF_STEP_ARG.QUEUE_LABEL)
#         module = importlib.import_module(script_path)
#         thread = threading.Thread(
#             target=module.main,
#             args=(procedure,),
#             name=script_path,
#             daemon=True,
#         )
#         thread.start()
#         caller = step[DEF_STEP_KEY.FUNC].value

#         header = Utils.procedure_get_header(procedure)
#         header[DEF_HEAD_KEY.THREADS].append((thread))
#         if use_join:
#             thread.join()

#         Engine.post_step_action_next(procedure)
#         log_msg = f"script completed. path: {script_path}"
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

#     def function_call(procedure):
#         step = Utils.procedure_get_active_step(procedure)
#         step_args = step[DEF_STEP_KEY.ARGS]
#         func_to_call = step_args[DEF_STEP_ARG.FUNCTION_POINTER]
#         args = step_args[DEF_STEP_ARG.ARGS]
#         Engine.post_step_action_next(
#             procedure
#         )  # NOTE: func_to_call() can change next_state
#         res = func_to_call(procedure, args)

#         return f"{func_to_call.__name__} -> '{res}'"

#     def subprocess_run_and_collect(procedure):
#         step = Utils.procedure_get_active_step(procedure)

#         step_label = step[DEF_STEP_KEY.LABEL]
#         step_args = step[DEF_STEP_KEY.ARGS]
#         cli_params = step_args[DEF_STEP_ARG.SUBPROCESS_PARAMS] or []
#         callback = step_args[DEF_STEP_ARG.SUBPROCESS_CALLBACK]

#         try:
#             # block the calling thread until command is returned
#             process = subprocess.run(
#                 cli_params,
#                 capture_output=True,
#                 text=True,
#             )
#         except Exception as e:
#             logger_step(procedure, f"{e}")
#             return

#         Engine.post_step_action_next(procedure)

#         result = process.stdout
#         if callable(callback):
#             return callback(procedure, result)

#     def popen(procedure):
#         step = Utils.procedure_get_active_step(procedure)
#         step_args = step[DEF_STEP_KEY.ARGS]
#         path = step_args[DEF_STEP_ARG.PATH]
#         args = step_args[DEF_STEP_ARG.ARGS]

#         # Utils.thread_define("my-caller", run_and_capture)

#         ###################################
#         process = subprocess.Popen(
#             [sys.executable, "-u", path, "child"],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,  # decode to string
#             bufsize=1,  # line-buffered
#         )
#         ###################################
#         header = Utils.procedure_get_header(procedure)
#         step_args = Utils.procedure_get_active_step_args(procedure)
#         header[DEF_HEAD_KEY.PROCESSES][path] = process

#         log_msg = f"pid: {process.pid}, path: {path}"
#         Engine.post_step_action_next(procedure)
#         return log_msg

#     def subprocess_call_and_wait(procedure):
#         step = Utils.procedure_get_active_step(procedure)

#         step_label = step[DEF_STEP_KEY.LABEL]
#         step_args = step[DEF_STEP_KEY.ARGS]
#         cli_params = step_args[DEF_STEP_ARG.SUBPROCESS_PARAMS] or []
#         callback = step_args[DEF_STEP_ARG.SUBPROCESS_CALLBACK]

#         try:
#             proc = subprocess.run(
#                 cli_params, stdout=subprocess.PIPE, capture_output=True, text=True
#             )
#             result = proc.stdout
#             callback(procedure, result)
#             # def worker(
#             #     procedure,
#             #     cli_params,
#             #     callback,
#             # ):

#             # worker_thread = threading.Thread(
#             #     target=worker,
#             #     args=(
#             #         procedure,
#             #         cli_params,
#             #         callback,
#             #     ),
#             #     daemon=True,
#             # )
#             # worker_thread.start()

#         except Exception as e:
#             logger_step(procedure, f"{e}")
#             return

#     def create_step_instrument_init(procedure):
#         step = Utils.procedure_get_active_step(procedure)
#         step_label = step[DEF_STEP_KEY.LABEL]
#         instrument_conf = step[DEF_STEP_KEY.ARGS]["instrument_conf"]
#         callback = step[DEF_STEP_KEY.ARGS]["callback"]
#         # cli_params = step_args[DEF_STEP_ARG.SUBPROCESS_PARAMS] or []
#         # callback = step_args[DEF_STEP_ARG.SUBPROCESS_CALLBACK]

#         new_instrument = instrument_factory(instrument_conf)
#         Engine.post_step_action_next(procedure)

#         if callable(callback):
#             callback(procedure, new_instrument)

step_functions = {
    # DEF_STEP_OP.DELAY_SET: time_load,
    # DEF_STEP_OP.DELAY_CHECK: time_check,
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
    STEP.FCALL: function_call,
    STEP.DELAY_START: delay_start,
    STEP.DELAY_WAIT: delay_check,
    STEP.WORKER_START: worker_start,
    STEP.WORKER_WAIT: worker_check,
    # DEF_STEP_OP.SUBPROCESS_RUN_AND_COLLECT: subprocess_run_and_collect,
    # DEF_STEP_OP.POPEN: popen,
    # DEF_STEP_OP.INSTRUMENT_INIT: create_step_instrument_init,
    # DEF_STEP_OP.PRINT: _print,
    # DEF_STEP_OP.QUEUE_CREATE: _queue_create,
}
