# from engine.constants import DEF_STEP_OP
# from engine.utils import Utils

# from typing import TYPE_CHECKING
from instruments.instrument import Instrument

# if TYPE_CHECKING:


class Dmm(Instrument):
    # DEF_MODEL_K2000 = "K2000"
    # DEF_MODEL_K2100 = "K2100"
    # DEF_MODEL_34401 = "34401"
    # all_dmm_models = [DEF_MODEL_K2000, DEF_MODEL_K2100]

    def __init__(self, instrument):
        super().__init__(instrument)
        _MODEL = self.Models.DMM_MODEL_K2000

    def setup(self):
        pass

    def api_get_voltage(self):
        return self.request(":MEASURE:VOLTAGE:DC?")
        # return float(res)

    def api_get_resistance(self):
        self.request(":MEASURE:RESISTANCE?")

    def api_get_diode(self):
        self.request(":MEASURE:DIODE?")

    def api_get_voltage_precision(self, precision=0.1):
        self.request(f":MEASURE:VOLTAGE:DC? ...({precision})...")

        K_MODELS = [self.Models.DMM_MODEL_K2000, self.Models.DMM_MODEL_K2100]
        if self._model in K_MODELS:
            return self.request(":MEAS:VOLT:DC?")

        self.request("CONF:VOLT:DC")
        self.request("VOLT:DC:NPLC " + str(precision))
        return self.request("READ?")

    def api_load_setup(self):
        if self._model == self.Models.DMM_MODEL_34401:
            return self.request("*ESE 60;*SRE 56;*CLS;:STAT:QUES:ENAB 32767")
        else:
            return self.api_rst_and_opc()

    def api_configure(self, dmm_mode):
        if self._model == self.Models.DMM_MODEL_K2000:
            if dmm_mode == "D":
                self.request(':FUNC "DIOD";:DIOD:CURR:RANG 0.001')
            else:
                self.request(
                    ':FUNC "VOLT:DC";:VOLT:DC:DIG 7;:VOLT:DC:NPLC 1.000000;:VOLT:DC:RANG:AUTO ON;:VOLT:DC:AVER:STAT OFF;:VOLT:DC:REF:STAT OFF;'
                )

            self.request("*SRE 1;:STAT:MEAS:ENAB 32;*CLS;")
            self.request("*SRE 48;")
            self.request(":FORM ASC;:FORM:ELEM READ,UNIT,CHAN;")
            res = self.request(":SENS:DATA?")
            res = res.split(",")
            res[0] = res[0].replace("VDC", "")
            return "{:.5f}".format(float(res[0]))

        elif self._model == self.Models.DMM_MODEL_K2100:
            if dmm_mode == "D":
                self.request(':FUNC "DIOD";')
            else:
                self.request(
                    ':FUNC "VOLT:DC";:VOLT:DC:NPLC 0.020000;:VOLT:DC:RANG:AUTO ON;:SENS:AVER:STAT OFF;'
                )

            self.request(":TRIG:SOUR IMM;:SAMP:COUN 1;:TRIG:COUN 1;:TRIG:DEL:AUTO ON;")
            dmm_result = self.request("READ?")
            dmm_result = dmm_result.split(",")
            dmm_result[0] = dmm_result[0].replace("VDC", "")
            return "{:.5f}".format(float(dmm_result[0]))

        elif self._model == self.Models.DMM_MODEL_34401:
            if dmm_mode == "D":
                self.request(":CONF:DIOD")
            else:
                self.request(":CONF:VOLT:DC")

            self.request(":TRIG:SOUR IMM;:SAMP:COUN 1;:TRIG:COUN 1;:TRIG:DEL:AUTO ON;")

            self.request(":TRIG:SOUR IMM;:TRIG:DEL:AUTO ON;")
            self.request(":TRIG:COUN 1;:SAMP:COUN 1;")
            dmm_result = float(self.connection.query("READ?"))
            return "{:.5f}".format(float(dmm_result))

    # @staticmethod
    # def create_step_get_voltage(step_label=""):
    #     return (Utils.create_step(DEF_STEP_OP.SCPI_REQUEST, step_label, {}),)
