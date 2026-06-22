from typing import TYPE_CHECKING, Any, Tuple, NewType, TypeAlias, TypedDict

from project.instruments.types.instrument_scope import Scope
from project.instruments.types.instrument_dmm import Dmm
from project.instruments.types.instrument_power_supply import PowerSupply

_DEF_REG_ADDRESS = 0
_DEF_BIT_INDEX = 1

RegisterAddress = int
BitIndex = int
BitAddress = NewType("BitAddress", Tuple[RegisterAddress, BitIndex])
BitValue = bool

AnyInstrument: TypeAlias = Scope | Dmm | PowerSupply


def extract_bit_address(bit_address: BitAddress) -> Tuple[RegisterAddress, BitIndex]:
    return bit_address[_DEF_REG_ADDRESS], bit_address[_DEF_BIT_INDEX]
