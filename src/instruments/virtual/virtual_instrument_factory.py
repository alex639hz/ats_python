# from virtual.virtual_scope import VirtualScope
from instruments.instrument import Instrument
from instruments.instrument_type import InstrumentType
from instruments.virtual.virtual_dmm import VirtualDmm
from instruments.virtual.virtual_scope import VirtualScope
from instruments.virtual.virtual_power_supply import VirtualPowerSupply


def virtual_instrument_factory(instrument: Instrument):

    instrument_type = InstrumentType(instrument._type)
    if instrument_type is InstrumentType.SCOPE:
        return VirtualScope(instrument)
    elif instrument_type is InstrumentType.PS:
        return VirtualPowerSupply(instrument)
    elif instrument_type is InstrumentType.DMM:
        return VirtualDmm(instrument)
    else:
        raise Exception(
            f"Virtual Instrument Factory got unknown instrument_type: {instrument_type}"
        )
