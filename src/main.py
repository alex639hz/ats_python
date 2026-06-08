import time

from engine.framework import framework
from project import project

try:

    procedure = project.create_procedure_with_builder("test procedure")
    framework.procedure_append(procedure)
    SHOULD_START_API_SERVER = False
    if SHOULD_START_API_SERVER:
        framework.start_api_server()
    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- Main TERMINATED ----- ")
