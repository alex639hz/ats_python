from enum import Enum
from pathlib import Path

NOARG = {}
DEF_NO_LABEL = ""
DEF_OK = "OK"
APP_FOLDER = Path("C:/ats_python")
LOG_FOLDER = Path("C:/ats_log")


class DEF_CMD(Enum):
    NULL = "NULL"
    PROCEDURE_RESTART = "PROCEDURE_RESTART"
    PROCEDURE_PLAY = "PROCEDURE_PLAY"
    PROCEDURE_PAUSE = "PROCEDURE_PAUSE"
    PROCEDURE_APPEND = "PROCEDURE_APPEND"
    INIT_INSTRUMENTS_FROM_JSON = "INIT_INSTRUMENTS_FROM_JSON"
    EXIT = "EXIT"


class STEP(Enum):
    NULL = "NULL"  # do-nothing operation
    PROCEDURE_START = "PROCEDURE_START"  # start procedure
    PROCEDURE_STOP = "PROCEDURE_STOP"  # stop procedure
    JUMP_TO_STEP = "JUMP_TO_STEP"  # jump to step by label
    ENGINE_STOP = "ENGINE_STOP"  # exit engine app
    EXIT = "EXIT"  # exit app
    DELAY_START = "TIMER_START"  # start a timer
    DELAY_WAIT = "TIMER_WAIT"  # wait for a timer to complete
    SCRIPT_RUN = "SCRIPT_RUN"  # execute external script
    SCPI_REQUEST = "SCPI_REQUEST"  # send a scpi command to a device
    FUNCTION_CALL = "FUNCTION_CALL"  # call a user function
    WORKER_START = "START_WORKER"  # call a user function as thread
    WORKER_WAIT = "WAIT_WORKER"  # call a user function as thread

    # execute subprocess  as cli command, wait for completion and collect stdout as text
    SUBPROCESS_RUN_AND_COLLECT = "SUBPROCESS_RUN_AND_COLLECT"

    # execute subprocess as cli command don't wait for completion (stdout can be collected using another function process header)
    POPEN = "POPEN"


class DEF_QUEUE_OP(Enum):
    CONSUME = "CONSUME"
    COMPLETE = "COMPLETE"


class DEF_STEP_KEY(Enum):
    LABEL = "LABEL"
    FUNC = "FUNC"
    ARGS = "ARGS"


class DEF_PROC_PARAM(Enum):
    IS_FIRST_RUN = "IS_FIRST_RUN"
    DATA = "DATA"
    STEP_IDX = "STEP_IDX"  # store procedure index
    NEXT_STATE = "NEXT_STATE"  # store next state of procedure execution
    SHOULD_RUN = "SHOULD_RUN"  # play/pause flag of procedure execution
    TIMESTAMP = "TIMESTAMP"  # used for time delay step function
    TIMER_ELAPSED_SECONDS = "TIMER_ELAPSED_SECONDS"
    QUEUES = "QUEUES"  # store list of queues
    THREADS = "THREADS"  # store list of threads
    PARAMS = "PARAMS"  # store params for procedure initialized using json file
    FOR_LOOP_INDEX = "FOR_LOOP_INDEX"
    PROCESSES = "PROCESS"


class STEP_ARG(Enum):
    DURATION_SECONDS = "TIMER_TARGET_SECONDS"
    NEXT_LABEL = "NEXT_LABEL"
    PATH = "SCRIPT_PATH"
    WAIT_THREAD = "WAIT_THREAD"
    QUEUE_LABEL = "QUEUE_LABEL"
    LOOP_INDEX = "LOOP_INDEX"
    SCPI_CMD = "SCPI_CMD"
    SCPI_INSTRUMENT = "SCPI_INSTRUMENT"
    FOR_LOOP_LIMIT = "NUM_OF_ITERATIONS"
    STEP_TO_RETURN = "STEP_TO_RETURN"
    FUNCTION = "FUNCTION_POINTER"
    ARGS = "FUNCTION_ARGS"
    TITLE = "FUNCTION_TITLE"
    SUBPROCESS_PARAMS = "SUBPROCESS_PARAMS"
    SUBPROCESS_CALLBACK = "SUBPROCESS_CALLBACK"


class DEF_NEXTSTATE_OP(Enum):

    WAIT = "WAIT"  # repeat current step again
    STAY = "STAY"  # repeat current step again
    NEXT = "NEXT"  # continue to next state
    JUMP = "JUMP"  # jump to step by label
    ERROR = "ERROR"  # enter error state TODO define
    PAUSE = "PAUSE"  # pause procedure - set should_run to false
    PLAY = "PLAY"  # continue to execute procedure - set should_run to true
    EXIT = "EXIT"  # exit procedure - set should_run to true


class VisaCommandReturnType(Enum):
    NONE = "NONE"
    FLOAT = "FLOAT"
    INT = "INT"
    STRING = "STRING"


class DEF_SCPI_COMMANDS(Enum):
    IDN = "*IDN?"
