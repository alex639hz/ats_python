from engine.framework import framework
from project.project import Project as MyProject

SHOULD_START_API_SERVER = False

try:
    SHOULD_IMPORT = True
    # if SHOULD_IMPORT:

    project = MyProject(framework)
    project.export()

    if SHOULD_START_API_SERVER:
        framework.start_api_server()

    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- KeyboardInterrupt ----- ")
except Exception as err:
    msg = f" ----- Main EXCEPTION: Error: {err}"
    print(f"main error: {msg}")
    framework.call_shutdown(msg)
