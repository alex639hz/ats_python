from engine.constants import *
from project.types import *
from engine.utils import *


class DutRegisterMap(Register):
    """Defines the register map of the DUT, with register addresses and bit positions."""

    BIT_ON: BitValue = True
    BIT_OFF: BitValue = False

    REG1 = RegisterAddress(0x0001)
    REG1_SETUP_A = 1
    REG1_SETUP_B = 3
    REG1_SETUP_C = 5
    REG2 = RegisterAddress(0x0002)
    REG2_SETUP_A = 4

    BIT0: BitAddress = BitAddress((REG2, 0))
    BIT1: BitAddress = BitAddress((REG2, 1))


class DutB(DutRegisterMap):

    def __init__(self):
        self.reg_store: dict[Any, int] = {}

    def open(self):
        self.connection = True

    def close(self):
        self.connection = False

    def register_write(self, address: RegisterAddress, value: int):
        self.reg_store[address] = value

    def register_read(self, address: RegisterAddress) -> int:
        return self.reg_store.get(address, 0)

    def bit_write(self, bit_address: BitAddress, value: BitValue):
        register_address, bit_idx = extract_bit_address(bit_address)
        init_value = self.register_read(register_address)
        register = Register(init_value)
        new_value = register.write_bit(bit_idx, value)
        self.register_write(register_address, new_value)
        return

    def bit_read(self, bit_address: BitAddress):
        register_address, bit_idx = extract_bit_address(bit_address)
        init_value = self.register_read(register_address)
        register = Register(init_value)
        return register.read_bit(bit_idx)
