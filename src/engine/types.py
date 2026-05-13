from typing import Tuple, NewType

_REG_ADDRESS = 0
_BIT_INDEX = 1

RegisterAddress = NewType("RegisterAddress", int)
BitIndex = NewType("BitIndex", int)
BitAddress = NewType("BitAddress", Tuple[RegisterAddress, BitIndex])
