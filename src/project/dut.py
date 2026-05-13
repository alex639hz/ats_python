from engine.constants import *
from engine.types import *
from engine.utils import *


class DutRegisterMap:
    """Defines the register map of the DUT, with register addresses and bit positions."""

    REG1 = RegisterAddress(0x0001)
    REG2 = RegisterAddress(0x0002)

    BIT0: BitAddress = BitAddress((REG2, BitIndex(0)))
    BIT1: BitAddress = BitAddress((REG2, BitIndex(1)))


class Dut:

    def __init__(self):
        self.reg_store = {}
        self.map = DutRegisterMap()

    def open(self):
        self.connection = True

    def close(self):
        self.connection = False

    def register_write(self, address: RegisterAddress, value: int):
        self.reg_store[address] = value

    def register_read(self, address: RegisterAddress):
        return self.reg_store.get(address, 0)

    def bit_write(self, bit_address: BitAddress, value: int):
        init_value = self.register_read(bit_address[0])
        reg = Register(init_value)
        res = reg.write_bit(bit_address[1], value)
        final_value = self.register_write(bit_address[0], res)

    def bit_read(self, address: RegisterAddress, bit_idx: BitIndex):
        init_value = self.register_read(address)
        reg = Register(init_value)
        return reg.read_bit(bit_idx)
