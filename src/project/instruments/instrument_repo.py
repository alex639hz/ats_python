import logging
from typing import TYPE_CHECKING, Any

# from instruments.instrument_repo import repository

# from engine.instruments.types.instrument_thermal_head import InstrumentThermalHead

# AnyInstrument = InstrumentDmm | InstrumentPowerSupply | InstrumentScope

if TYPE_CHECKING:
    from project.instruments.instrument import Instrument

# if TYPE_CHECKING:
#     from engine.instruments.instrument_factory import AnyInstrument

logger = logging.getLogger(__name__)


class InstrumentRepo:

    repo: dict[str, Any] = {}

    def __init__(self):
        pass

    def add(self, instrument: Instrument):
        self.repo[instrument._label] = instrument

    def get_by_label(self, label) -> Any:
        inst = self.repo.get(label)  # type: ignore
        return inst

    def get_instrument_by_label(self, label) -> Any:
        inst = self.get_by_label(label)  # type: ignore

        if inst is None:
            raise Exception(f"instrument not found: {label}")

        return inst

    def get_all_labels(self):
        res = []
        for label in self.repo.keys():
            res.append(label)
        return res

    def request_all_instruments_model(self):
        res = []
        for instrument_label, instrument_instance in self.repo.items():
            res.append(instrument_instance.api_std_idn())
        return res

    @staticmethod
    def is_instance_of_or_throw(instrument: Instrument, instance: Any) -> bool:
        if not isinstance(instrument, instance):
            raise Exception(
                f"incorrect instrument type: {instrument._label} is not an instance of {instance.__name__}"
            )
        return True

    def instrument_factory(self, instrument={}):

        from project.instruments.instrument_type import InstrumentType
        from project.instruments.types.instrument_dmm import Dmm
        from project.instruments.types.instrument_power_supply import PowerSupply
        from project.instruments.types.instrument_scope import Scope

        existing_instrument = repository.get_by_label(instrument["label"])
        if existing_instrument:
            return existing_instrument

        instrument_type = instrument["type"]
        if instrument_type == InstrumentType.DMM.value:
            new_instrument = Dmm(instrument)
        elif instrument_type == InstrumentType.PS.value:
            new_instrument = PowerSupply(instrument)
        elif instrument_type == InstrumentType.SCOPE.value:
            new_instrument = Scope(instrument)
        elif instrument_type == InstrumentType.THERMAL_HEAD.value:
            # return InstrumentThermalHead(instrument)
            pass
        else:
            raise Exception(f"Unknown instrument type: {instrument_type}")

        self.add(new_instrument)

        return new_instrument


repository = InstrumentRepo()
