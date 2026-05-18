from typing import TYPE_CHECKING, Any, Tuple, NewType, TypedDict

if TYPE_CHECKING:
    from engine.procedure import Procedure

_REG_ADDRESS = 0
_BIT_INDEX = 1

RegisterAddress = NewType("RegisterAddress", int)
BitIndex = NewType("BitIndex", int)
BitAddress = NewType("BitAddress", Tuple[RegisterAddress, BitIndex])


class StepInterface(TypedDict):
    procedure: Procedure
    args: dict[str, Any]
