import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from instruments.instrument import Instrument

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


repository = InstrumentRepo()
