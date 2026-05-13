from typing import Any, Tuple, NewType

from engine.procedure import Procedure

_REG_ADDRESS = 0
_BIT_INDEX = 1

RegisterAddress = NewType("RegisterAddress", int)
BitIndex = NewType("BitIndex", int)
BitAddress = NewType("BitAddress", Tuple[RegisterAddress, BitIndex])
WorkerArgs = NewType("WorkerArgs", tuple[Procedure, dict[str, Any]])
