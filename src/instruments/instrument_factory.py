from instruments.instrument_type import InstrumentType
from instruments.types.instrument_dmm import Dmm
from instruments.types.instrument_power_supply import PowerSupply
from instruments.types.instrument_scope import Scope
from instruments.instrument_repo import repository

# from engine.instruments.types.instrument_thermal_head import InstrumentThermalHead

# AnyInstrument = InstrumentDmm | InstrumentPowerSupply | InstrumentScope


def instrument_factory(instrument={}):
    existing_instrument = repository.get_by_label(instrument["label"])
    if existing_instrument:
        return existing_instrument

    instrument_type = instrument["type"]
    if instrument_type == InstrumentType.DMM.value:
        inst = Dmm(instrument)
    elif instrument_type == InstrumentType.PS.value:
        inst = PowerSupply(instrument)
    elif instrument_type == InstrumentType.SCOPE.value:
        inst = Scope(instrument)
    elif instrument_type == InstrumentType.THERMAL_HEAD.value:
        # return InstrumentThermalHead(instrument)
        pass
    else:
        raise Exception(f"Unknown instrument type: {instrument_type}")

    repository.add(inst)

    return inst
