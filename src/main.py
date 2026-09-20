"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

from engine.framework import framework
from project.project import Project

SHOULD_START_API_SERVER = False
if SHOULD_START_API_SERVER:
    framework.start_api_server()

project = Project()

try:

    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- KeyboardInterrupt ----- ")
except Exception as err:
    msg = f" ----- Main EXCEPTION: Error: {err}"
    print(f"main error: {msg}")
