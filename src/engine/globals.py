from enum import Enum
from pathlib import Path
from typing import Any


class DEF_GLOBAL_SECTIONS(Enum):
    FLAGS = "FLAGS"
    QUEUES = "QUEUES"
    SIGNALS = "SIGNALS"
    INSTRUMENTS = "INSTRUMENTS"
    SESSION = "ACTIVE_PROCESS"
    PATHS = "PATHS"


class DEF_GLOBAL_QUEUE(Enum):
    Q_LOG = "Q_LOG"
    Q_ENG = "Q_ENG"


# class DEF_GLOBAL_FLAGS(Enum):
#     ENG_RUN = "ENG_RUN"


class DEF_GLOBAL_SIGNALS(Enum):
    GUI_UPDATE = "GUI_UPDATE"


class DEF_GLOBAL_SESSION_FIELDS(Enum):
    SESSION_LABEL = "SESSION_LABEL"
    ACTIVE_PROCEDURE = "ACTIVE_PROCEDURE"
    ACTIVE_STEP = "ACTIVE_STEP"
    TIMESTAMP_SESSION_START = "TIMESTAMP_SESSION_START"
    TIMESTAMP_SESSION_END = "TIMESTAMP_SESSION_END"


class DEF_GLOBAL_PATHS(Enum):
    RECORDS_BASE_PATH = "RECORDS_BASE_PATH"


class Globals:
    store = {
        DEF_GLOBAL_SECTIONS.FLAGS: {},
        DEF_GLOBAL_SECTIONS.QUEUES: {},
        DEF_GLOBAL_SECTIONS.SESSION: {
            DEF_GLOBAL_SESSION_FIELDS.ACTIVE_PROCEDURE: [],
            DEF_GLOBAL_SESSION_FIELDS.ACTIVE_STEP: {},
            DEF_GLOBAL_SESSION_FIELDS.TIMESTAMP_SESSION_START: None,
            DEF_GLOBAL_SESSION_FIELDS.TIMESTAMP_SESSION_END: None,
        },
        DEF_GLOBAL_SECTIONS.PATHS: {
            DEF_GLOBAL_PATHS.RECORDS_BASE_PATH: "C:/ATS_DATA",
        },
    }

    class DefFlagKeys:
        IS_RUNNING = "IS_RUNNING"
        IS_GUI = "IS_GUI"

    def __init__(self):
        pass

    def flag_set(self, key, value):
        self.store[DEF_GLOBAL_SECTIONS.FLAGS][key] = value

    def flag_get(self, key):
        return self.store[DEF_GLOBAL_SECTIONS.FLAGS][key]

    def q_set(self, key, value):
        self.store[DEF_GLOBAL_SECTIONS.FLAGS][key] = value

    def q_get(self, key):
        return self.store[DEF_GLOBAL_SECTIONS.FLAGS][key]

    def set_field_by_section_and_key(self, section, key, value):
        self.store[section][key] = value

    def get_field_by_section_and_key(self, section, key) -> Any:
        if section not in self.store.keys() or key not in self.store[section].keys():
            return None
        return self.store[section][key]

    def get_session(self):
        return self.store[DEF_GLOBAL_SECTIONS.SESSION]

    # def get_session(self, section, key):
    #     return self.get[DEF_GLOBAL_SECTIONS.SESSION][key]


global_context = Globals()
