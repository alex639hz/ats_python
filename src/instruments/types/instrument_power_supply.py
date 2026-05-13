import time
import logging
from engine.constants import DEF_STEP
from engine.utils import Utils
from instruments.instrument import Instrument
from instruments.instrument_repo import repository

logger = logging.getLogger("instrument_power")


OUTPUT_ON = True
OUTPUT_OFF = False

"""
    InstrumentPowerSupply class defined per channel not par device. 
    ie. for an instrument with N channels, there will be N instances of InstrumentPowerSupply. 
"""


class PowerSupply(Instrument):
    DEF_CHANNEL_STATE_OFF = 0
    DEF_CHANNEL_STATE_ON = 1
    _model = "N6700C"
    _channel = 0
    _total_channels = 1
    _voltage = 0

    def __init__(self, instrument):
        super().__init__(instrument)

    def api_set_channel_state(self, state):
        # state = "ON" if state else "OFF"
        self.request(f"OUTPUT {self._channel} {state}")

    def api_deactivate(self):
        off = PowerSupply.DEF_CHANNEL_STATE_OFF
        self.api_set_channel_state(off)
        # logger.info(f"{self._label} is off")

    def api_activate(self):
        on = PowerSupply.DEF_CHANNEL_STATE_ON
        self.api_set_channel_state(on)
        # logger.info(f"{self._label} is on")

    def api_set_voltage_limit(self, volt):
        logger.info(f"{self._label} voltage limit set: {volt}")
        pass

    def api_set_voltage(self, volt):
        logger.info(f"{self._label} voltage set: {volt}")

    def api_set_current(self, amper):
        logger.info(f"{self._label} current set: {amper}")

    def setup(self):
        pass

    @staticmethod
    def create_step_api_set_channel(step_label):
        # return (Utils.create_step(DEF_STEP_OP.SCPI_REQUEST, step_label, {}),)
        pass

    @staticmethod
    def convert_list_to_comma_delimited_string(*channels):
        res = ""
        for channel in channels:
            res += str(channel)
            if channel != channels[-1]:
                res += ","
            # print("channel: ", channel)
        return res
