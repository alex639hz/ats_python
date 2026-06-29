from engine.framework import framework

try:

    SELECTED_PROJECT = "project_1"

    SHOULD_APPEND_PROCEDURE = True
    if SHOULD_APPEND_PROCEDURE:
        if SELECTED_PROJECT == "project_2":
            from project_2.project import Project2

            project = Project2(framework)
        else:
            from project.project import Project

            project = Project(framework)
        project.export()

    SHOULD_START_API_SERVER = True
    if SHOULD_START_API_SERVER:
        framework.start_api_server()

    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- Main TERMINATED ----- ")
except Exception as e:
    framework.call_shutdown(f" ----- Main EXCEPTION: Error: {e} ----- ")
