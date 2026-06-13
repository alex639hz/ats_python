from datetime import datetime
from typing import TYPE_CHECKING

from engine.constants import *
from engine.utils import *

if TYPE_CHECKING:
    from engine.framework import Framework


COLLECTION_SESSION = "session"


class Context:
    def __init__(self, owner: Procedure | Framework):
        self._context: dict[str, Any] = {}
        self._context_id = ""

        self.owner = owner
        pass

    def create(self, session_args: dict[str, Any] = {}, insert_db=True):
        """Creates a session for the procedure.
        The session dictionary stored in the procedure instance and used as data store during procedure execution.
        The session can be stored in the database if insert_db is True.
        """
        context = {
            "created_at": datetime.now(),
            "owner_label": self.owner.get_label(),
            **session_args,
        }
        self._context = context

        IGNORE_DB = True
        if not IGNORE_DB:
            self.prepare_session()

            if insert_db:
                res = self.owner.db.insert_one("session", self._context)
                self._context_id = res.inserted_id

        return context

    def prepare_session(self):
        from engine.procedure import Procedure

        if isinstance(self.owner, Procedure):
            res_session = {
                "created_at": self._context.get("created_at"),
                "owner_label": self._context.get("owner_label"),
                "test_cases": self._context.get("test_cases"),
            }
        elif isinstance(self.owner, Framework):
            res_session = {
                "created_at": self._context.get("created_at"),
                "owner_label": self._context.get("owner_label"),
                "test_cases": self._context.get("test_cases"),
            }
        else:
            raise Exception("invalid session owner instance")

        return res_session

    def db_update(self):
        _id = self._context_id

        if not _id:
            raise Exception(f"session_id is not set: {self.owner.collection_name}")

        res_session = self.prepare_session()

        res = self.owner.db.update_one(
            self.owner.collection_name, {"_id": _id}, {**res_session}
        )

        return res

    def attribute_set(self, name, value, db_update=False):
        """Sets the session data for the procedure."""
        self._context[name] = value

        if db_update:
            self.db_update()

        return self

    def attribute_get(self, name) -> Any:
        return self._context.get(name)
