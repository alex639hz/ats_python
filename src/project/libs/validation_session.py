"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

from engine.constants import DEF_DB_COL_SESSION, DEF_DB_COL_TEST
from engine.framework import framework

DEF_PASS = True
DEF_FAIL = not DEF_PASS


class ValidationSession:

    def __init__(self, session: dict, init_db: bool = True):
        self.cases = session["cases"]
        self.label = session["label"]
        self.index = 0
        self.results = []
        # self.results_status = False
        # self.results_payload = None
        self.db = framework.db
        self.created_at = framework.get_time_datetime()
        self.status: bool
        session_db = {
            "label": self.label,
            "cases": self.cases,
            "created_at": self.created_at,
        }
        if init_db:
            res = self.db._collection(DEF_DB_COL_SESSION).insert_one(session_db)
            self.id = res.inserted_id
        pass

    def load_test(self):
        """set new test in db"""
        test_init = self.cases[self.index]
        test = {}
        test["payload"] = test_init
        test["created_at"] = framework.get_time_datetime()
        res = self.db._collection(DEF_DB_COL_TEST).insert_one(test)
        self.test_id = res.inserted_id
        self.test = test
        pass

    def test_set_pass(self):
        self.test_update_result(DEF_PASS)

    def test_set_fail(self):
        self.test_update_result(DEF_FAIL)

    def test_update_result(self, state: bool):
        self.test_status = state
        self.db.update_one(DEF_DB_COL_TEST, {"_id": self.test_id}, {"result": state})

        self.results.append(state)
        pass

    def session_update_result(self):
        self.db.update_one(
            DEF_DB_COL_SESSION, {"_id": self.id}, {"result": self.results}
        )

        pass

    def increase_index(self):
        max = len(self.cases)
        in_range = self.index < max - 1

        results_size = len(self.results)

        # if not (self.index < results_size):
        #     return False

        if not in_range:
            return False
        self.index = self.index + 1
        return True

    def get_active_case(self):
        test_case = self.cases[self.index]
        return test_case
