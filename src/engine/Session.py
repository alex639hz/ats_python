from datetime import datetime
from time import time
from typing import TYPE_CHECKING
import logging


from engine.constants import *
from engine.utils import *
from engine.step import Step
from engine.worker import Worker

from engine.db import Db, database

if TYPE_CHECKING:
    from engine.framework import Framework

COLLECTION_SESSION = "session"


class Session:
    def __init__(self, owner: Procedure | Framework):
        self._session: dict[str, Any] = {}
        self._session_id = ""

        self.owner = owner
        pass

    def create(self, session_args: dict[str, Any] = {}, insert_db=True):
        """Creates a session for the procedure.
        The session dictionary stored in the procedure instance and used as data store during procedure execution.
        The session can be stored in the database if insert_db is True.
        """
        session = {
            "created_at": datetime.now(),
            "owner_label": self.owner.get_label(),
            **session_args,
        }

        if insert_db:
            res = self.owner.db.insert_one("session", session)
            self._session_id = res.inserted_id

        self._session = session

        return session

    def db_update(self):
        _id = self._session_id

        if not _id:
            raise Exception("session_id is not set, cannot update session in db")

        res = self.owner.db.update_one(
            COLLECTION_SESSION, {"_id": _id}, {**self._session}
        )

        return res

    def attribute_set(self, name, value, db_update=False):
        """Sets the session data for the procedure."""
        self._session[name] = value

        if db_update:
            self.db_update()

        return self

    def attribute_get(self, name) -> Any:
        return self._session.get(name)
