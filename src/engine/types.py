from typing import TYPE_CHECKING, Any, Tuple, NewType, TypeAlias, TypedDict

from instruments.types.instrument_scope import Scope
from instruments.types.instrument_dmm import Dmm
from instruments.types.instrument_power_supply import PowerSupply

if TYPE_CHECKING:
    from engine.procedure import Procedure

_REG_ADDRESS = 0
_BIT_INDEX = 1

RegisterAddress = NewType("RegisterAddress", int)
BitIndex = NewType("BitIndex", int)
BitAddress = NewType("BitAddress", Tuple[RegisterAddress, BitIndex])

AnyInstrument: TypeAlias = Scope | Dmm | PowerSupply


class StepInterface(TypedDict):
    procedure: Procedure
    args: dict[str, Any]
