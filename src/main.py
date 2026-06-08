import time

from engine.framework import framework
from project import project

try:

    procedure = project.create_procedure_with_builder("test procedure")
    procedure.stop()

    SHOULD_APPEND_PROCEDURE = True
    if SHOULD_APPEND_PROCEDURE:
        framework.procedure_template_append(procedure)
        procedure1 = framework.procedure_template_get(procedure.get_label())
        pass

    SHOULD_START_API_SERVER = False
    if SHOULD_START_API_SERVER:
        framework.start_api_server()

    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- Main TERMINATED ----- ")
