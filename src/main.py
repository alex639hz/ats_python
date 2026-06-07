from engine.framework import framework
from project import project

try:

    procedure = project.create_procedure_with_builder("test procedure")
    framework.procedure_append(procedure)
    framework.start_api_server()
    framework.run()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- Main TERMINATED ----- ")
