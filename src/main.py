from engine.framework import framework
from engine.procedure import Procedure
from project import project

try:

    procedure = project.create_procedure_with_builder("my-dut-test")

    SHOULD_APPEND_PROCEDURE = True
    if SHOULD_APPEND_PROCEDURE:
        framework.procedure_append(procedure)
        procedure.start()

    SHOULD_START_API_SERVER = False
    if SHOULD_START_API_SERVER:
        framework.start_api_server()

    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- Main TERMINATED ----- ")
except Exception as e:
    framework.call_shutdown(f" ----- Main EXCEPTION: Error: {e} ----- ")
