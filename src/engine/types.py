from typing import TYPE_CHECKING, Any, Tuple, NewType, TypeAlias, TypedDict

if TYPE_CHECKING:
    from engine.procedure import Procedure

from typing import Any, TypeAlias

Args: TypeAlias = dict[str, Any]


class StepInterface(TypedDict):
    procedure: Procedure
    args: Args


class LogInterface(TypedDict):
    msg: str
    args: Args
