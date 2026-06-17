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

    def create(self, session_args: dict[str, Any] = {}):
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
        return self._context
    
    def get_context(self):
        return self._context
    
    def attribute_set(self, name, value):
        """Sets the session data for the procedure."""
        self._context[name] = value

        return self

    def attribute_push(self, name, value):

        attribute: Any | None = self._context.get(name)

        if attribute is None or not isinstance(attribute, list):
            self._context[name] = []

        # array: list =
        self._context[name].append(value)

        return self

    def attribute_get(self, name) -> Any:
        return self._context.get(name)
