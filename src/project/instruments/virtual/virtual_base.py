import math
from project.instruments.instrument import Instrument
import logging

logger = logging.getLogger("[V_Scope]")


class VirtualInstrumentBase:
    def __init__(self, instrument: Instrument) -> None:
        self._label = instrument._label
        self._instrument = instrument
        # logger.info(f"VirtualInstrumentBase: {self._label}")
