from typing import TYPE_CHECKING, Any, Tuple, NewType, TypeAlias, TypedDict

if TYPE_CHECKING:
    from engine.procedure import Procedure


class StepInterface(TypedDict):
    procedure: Procedure
    args: dict[str, Any]
