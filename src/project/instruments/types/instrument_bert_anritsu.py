import time

DEF_USE_VIRTUAL_PYVISA = True
DEF_DEFAULT_VISA_TIMEOUT_MS = 10_000

if DEF_USE_VIRTUAL_PYVISA:
    import engine.virtual_pyvisa as pyvisa
else:
    import pyvisa

from enum import Enum
from engine.constants import STEP
from engine.utils import Utils
from engine.instruments.instrument import Instrument


class InstrumentBertAnritsu(Instrument):
    class DEF_MODULATION_TYPE:
        NRZ = "NRZ"
        PAM3 = "PAM3"
        PAM4 = "PAM4"

    DEFAULT_MODULATION = DEF_MODULATION_TYPE.NRZ

    def __init__(self, instrument):
        super().__init__(instrument)
        self.modulation_type = (
            instrument.get("modulation_type")
            or InstrumentBertAnritsu.DEFAULT_MODULATION
        )
        self.selected_module = 0

    def api_set_module(self, module_id):
        self.request(":MODule:ID " + str(module_id))
        self.selected_module = module_id

    def api_get_modulation_type(self):
        return self.request(":SOURce:MODulation:TYPE?")

    def api_set_jitter_clock_source(self, module_id=4, clock_source_type="INT1"):
        # Note: INT1, INT2, EXT, need to be INT1 -> Unit1:Slot2:MU181000A
        self.request(":SYSTem:INPut:CSELect " + str(clock_source_type))

    def api_get_jitter_clock_source(self):
        return self.request(":SYSTem:INPut:CSELect?")

    def api_set_ppg_clock_source(self, clock_source_type="INT2"):
        # INT1, INT2, EXT, need to be INT1 -> Unit1:Slot2:MU181000A
        self.request(":SYSTem:INPut:CSELect " + str(clock_source_type))

    def api_get_ppg_clock_source(self):
        # self.api_set_module(7)
        # time.sleep(0.1)
        message = self.connection.query(":SYSTem:INPut:CSELect?")
        return message

    def set_output_standard(self, mode="Variable"):
        self.api_set_module(7)
        time.sleep(0.1)
        # Variable, TBT1(10.3125), USB4_2(10), TBT2(20.625), USB4_3(20). we use Variable
        self.connection.write(':OUTPut:DATA:STANdard "' + str(mode) + '"')
        self.operationStatus = "set"
        return self.operationStatus

    def get_output_standard(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":OUTPut:DATA:STANdard?")
        return message

    def get_clock_source(self):
        message = self.connection.query(":SYSTem:INPut:CSELect?")
        return message

    def set_uentry_id(self):
        self.connection.write(":UENTry:ID 1;")
        self.operationStatus = "set"
        return self.operationStatus

    def set_interface(self, inter_num=1):
        self.connection.write(":INTerface:ID " + str(inter_num))
        self.operationStatus = "set"
        return self.operationStatus

    def get_output(self):
        message = self.connection.query(":SOURce:OUTPut:ASET?")
        return message

    def set_output(self, state):
        self.connection.write(":SOURce:OUTPut:ASET %s" % state)
        self.operationStatus = "set"
        return self.operationStatus

    def restore_setup(self, path, default_setup=False):
        if self._type == "bert_anritsu_mp1900":
            if default_setup:
                message = ":SYSTem:MEMory:INITialize"
            else:
                message = ':SYSTem:MMEMory:QRECall "%s"' % path
            self.connection.write(message)
        self.operationStatus = "set"
        return self.operationStatus

    # MODULE 7
    def set_modulation_type(self):
        # Example : {mod_type = "NRZ", "PAM3", "PAM4"}
        self.api_set_module(7)
        time.sleep(0.1)
        if "pam4" in self.mod_type.lower():
            self.mod_type = "PAM3"
        self.connection.write(":SOURce:MODulation:TYPE " + self.mod_type)
        self.operationStatus = "set"
        return self.operationStatus

    def enable_precoding(self, val):
        self.api_set_module(7)
        time.sleep(0.1)
        state = ["OFF", "ON"]
        str0 = ":SOURce:PATTern:PAM4:PREC %s" % state[val]
        self.connection.write(str0)
        self.operationStatus = "set"
        return self.operationStatus

    def enable_pattern_polarity(self, val):
        self.api_set_module(7)
        time.sleep(0.1)
        state = ["OFF", "ON"]
        str0 = f":SOURce:PATTern:PAM3:USB4:PINVerse {state[val]}"
        self.connection.write(str0)
        self.operationStatus = "set"
        return self.operationStatus

    def set_LFPS_USB4_swing(self, val=1):
        self.api_set_module(7)
        time.sleep(0.1)
        state = ["LOW", "HIGH"]
        str0 = f":SOURce:PATTern:PAM3:USB4:SWINg {state[val]}"
        self.connection.write(str0)
        self.operationStatus = "set"
        return self.operationStatus

    def set_LFPS_USB4_tPeriod(self, tPeriod=50):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:TPERiod {tPeriod}")
        self.operationStatus = "set"
        return self.operationStatus

    def get_LFPS_USB4_tPeriod(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(f":SOURce:PATTern:PAM3:USB4:TPERiod?")
        return message

    def set_LFPS_USB4_DC(self, DC=50):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:DUTY {DC}")
        self.operationStatus = "set"
        return self.operationStatus

    def get_LFPS_USB4_DC(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(f":SOURce:PATTern:PAM3:USB4:DUTY?")
        return message

    def set_LFPS_USB4_TPData(self, TPData=100):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:TPData {TPData}")
        self.operationStatus = "set"
        return self.operationStatus

    def get_LFPS_USB4_TPData(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(f":SOURce:PATTern:PAM3:USB4:TPData?")
        return message

    def set_LFPS_USB4_HS_data_pattern(self, pattern_type="PRBS11"):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:DATA {pattern_type}")
        self.operationStatus = "set"
        return self.operationStatus

    def start_LFPS_USB4(self):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:STRansmit")
        self.operationStatus = "set"
        return self.operationStatus

    def stop_LFPS_USB4(self):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:STOP")
        self.operationStatus = "set"
        return self.operationStatus

    def LFPS_USB4_break(self):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:PAM3:USB4:MANual")
        self.operationStatus = "set"
        return self.operationStatus

    def get_LFPS_USB4_state(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(f":SOURce:PATTern:PAM3:USB4:STATe?")
        return message

    def set_data_type(self, pattern_type):
        # PRBS/PRTS/DATA/USB4/USB4_G4_RFVTS
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:TYPE {pattern_type}")
        self.operationStatus = "set"
        return self.operationStatus

    def set_data_length(self, type, length):
        self.api_set_module(7)
        time.sleep(0.1)
        if type == "PRTS":
            str0 = ":SOURce:PATTern:PAM3:PRTS:LENG " + str(length)
        elif type == "PRBS":
            str0 = ":SOURce:PATTern:PAM4:PRBS:LENG " + str(length)
        else:
            print("Error: Unknown data type for SigGen", 0)
            return
        self.connection.write(str0)
        self.operationStatus = "set"
        return self.operationStatus

    def enable_error_insertion(self):
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface(1)
        time.sleep(0.1)
        self.connection.write(":SOURce:PATTern:EADDition:SET ON")
        self.operationStatus = "set"
        return self.operationStatus

    def disable_error_insertion(self):
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface(1)
        time.sleep(0.1)
        self.connection.write(":SOURce:PATTern:EADDition:SET OFF")
        self.operationStatus = "set"
        return self.operationStatus

    def set_error_insertion_variation(self, state="SINGle"):
        # string: SINGle/REPeat
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface(1)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:EADDition:VARiation {state}")
        self.operationStatus = "set"
        return self.operationStatus

    def get_error_insertion_variation(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:PATTern:EADDition:VARiation?")
        return message

    def set_error_insertion_source(self, state="EXTDisable"):
        # string: INTernal/EXTTrig/EXTDisable
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface(1)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:EADDition:SOURce {state}")
        self.operationStatus = "set"
        return self.operationStatus

    def get_error_insertion_source(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:PATTern:EADDition:SOURce?")
        return message

    def insert_single_error(self):
        # string: INTernal/EXTTrig/EXTDisable
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface(1)
        time.sleep(0.1)
        self.connection.write(f":SOURce:PATTern:EADDition:SINGle")
        self.operationStatus = "set"
        return self.operationStatus

    def set_pam4_even(self):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":OUTPut:PAM4:EVEN")
        self.operationStatus = "set"
        return self.operationStatus

    def set_total_amplitude(self, amplitude):
        # Working only with PAM3/4 modulation type
        # Example : amplitude = {0.070 to 0.800 Vp-p}
        self.api_set_module(7)
        time.sleep(0.1)
        # mod_type = self.get_modulation_type()
        # mod_type = "NRZ"
        if self.mod_type == "NRZ":
            self.connection.write(":OUTPut:DATA:AMPLitude DATA," + str(amplitude))
        else:
            self.connection.write(":OUTPut:PAM3:TOTal:AMPLitude " + str(amplitude))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_missmatch_Anritsu(self, missmatch_lower="50.0", missmatch_uppper=0):
        self.api_set_module(7)
        time.sleep(0.1)
        # mod_type = self.get_modulation_type()
        if self.mod_type == "NRZ":
            message = "!!! Wrong modulation type !!! No changes applied !!!"
            print(message)
        else:
            self.connection.write(
                ":OUTPut:PAM3:LOWer:AMPLitude:PERCent " + str(missmatch_lower)
            )
            time.sleep(2)
            # self.connection.write(':OUTPut:PAM3:UPPer:AMPLitude:PERCent ' + str(missmatch_uppper))
            # time.sleep(2)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_total_amplitude(self):
        self.api_set_module(7)
        time.sleep(0.1)
        # mod_type = "NRZ"
        if self.mod_type == "NRZ":
            message = self.connection.query(":OUTPut:DATA:AMPLitude? DATA")
        else:
            message = self.connection.query(
                f":OUTPut:{self.mod_type.upper()}:TOTal:AMPLitude?"
            )
        return message

    def set_ffe_settings_for_pam2(self):
        self.set_ffe_status("ON")
        self.set_preset_standard()

    def get_preset_standard(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:EMPHasis:STANdard?")
        return message

    def set_preset_standard(self, mode="USB4"):
        # Example : mode: USER\USB4\TBT3\...
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:STANdard %s" % mode)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ffe_status(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:EMPHasis:ENABle?")
        return message

    def set_ffe_status(self, status):
        # Example : status: ON/OFF
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:ENABle %s" % status)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ffe(self, coef):
        # Example : {coef = "C-2", "C-1", "C0", "C1"}
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:EMPHasis:COEFficient:VALUe? %s" % coef)
        return message

    def set_ffe(self, coef, value):
        # Example : {coef = "-2", "-1", "0", "1"} | {-1.0000 to 1.0000 / 0.0001 step}
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(
            ":SOURce:EMPHasis:COEFficient:VALUe %s," % coef + str(value)
        )
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ffe_all(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = (
            "C-2 = "
            + self.connection.query(":SOURce:EMPHasis:COEFficient:VALUe? C-2")
            + "\n"
        )
        time.sleep(0.1)
        message += (
            "C-1 = "
            + self.connection.query(":SOURce:EMPHasis:COEFficient:VALUe? C-1")
            + "\n"
        )
        time.sleep(0.1)
        message += (
            "C0	= "
            + self.connection.query(":SOURce:EMPHasis:COEFficient:VALUe? C0")
            + "\n"
        )
        time.sleep(0.1)
        message += "C1	= " + self.connection.query(
            ":SOURce:EMPHasis:COEFficient:VALUe? C1"
        )
        time.sleep(0.1)
        return message

    def set_ffe_all(self, cp1, c0, cm1, cm2=0):
        # Example : {-1.0000 to 1.0000 / 0.0001 step}
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:COEFficient:VALUe C-2," + str(cm2))
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:COEFficient:VALUe C-1," + str(cm1))
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:COEFficient:VALUe C0," + str(c0))
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:COEFficient:VALUe C1," + str(cp1))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_preset(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:EMPHasis:PRESet?")
        return message

    def set_preset(self, preset):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SOURce:EMPHasis:PRESet " + str(preset))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_bit_rate(self):
        self.api_set_module(7)
        time.sleep(0.1)
        # mod_type = self.get_modulation_type()
        # mod_type = "NRZ"
        if self.mod_type == "NRZ":
            message = self.connection.query(":OUTPut:DATA:BITRate?")
        else:
            message = self.connection.query(":OUTPut:PAM4:SRATe?")
        return message

    def set_bit_rate(self, value):
        # Example : value = {2.400000 to 64.200000 Gbit/s}
        if not 2.4 < value < 64.2:
            print("!!! Wrong Bit Rate value !!! No changes applied !!!")
            return
        self.api_set_module(7)
        time.sleep(0.1)
        # mod_type = self.get_modulation_type()
        # mod_type = "NRZ"
        if self.mod_type == "NRZ":
            self.connection.write(":OUTPut:DATA:BITRate " + str(value))
        else:
            mes = ":OUTPut:PAM4:SRATe " + str(value)
            self.connection.write(":OUTPut:PAM4:SRATe " + str(value))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_out_crate(self, mode="HALF"):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SYSTem:OUTPut:CRATe " + str(mode))
        time.sleep(0.1)
        self.operationStatus = "set"

    def get_out_crate(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SYSTem:OUTPut:CRATe?")
        time.sleep(0.1)
        return message

    def set_out_rclock_sel(self, mode="INT"):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":OUTPut:RCLock:SELect " + str(mode))
        time.sleep(0.1)
        self.operationStatus = "set"

    def get_out_rclock_sel(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":OUTPut:RCLock:SELect?")
        time.sleep(0.1)
        return message

    def set_pattern_type(self, type):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SOURce:PATTern:TYPE " + str(type))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_pattern_data_sq(self, length):
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":SOURce:PATTern:DATA:EDIT:LENG %s" % length)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def recall_pattern(self, path, file_type="TXT"):
        self.api_set_module(7)
        time.sleep(0.1)
        if path.lower().endswith(".txt"):
            path = path[:-4]
        command = ":SYSTem:MMEMory:PATTern:RECall " + '"' + path + '"' + f",{file_type}"
        self.connection.write(command)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_pattern_type(self):
        self.api_set_module(7)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:PATTern:TYPE?")
        return message

    def get_pattern_length(self):
        self.api_set_module(7)
        time.sleep(0.1)
        # mod_type = self.get_modulation_type()
        # mod_type = "NRZ"
        pat_type = self.connection.query(":SOURce:PATTern:TYPE?")
        if self.mod_type == "NRZ":
            message = self.connection.query(":SOURce:PATTern:%s:LENGth?" % pat_type)
        elif self.mod_type == "PAM3":
            message = self.connection.query(
                ":SOURce:PATTern:%s:%s:LENGth?" % (self.mod_type, pat_type)
            )
        elif self.mod_type == "PAM4":
            message = self.connection.query(
                ":SOURce:PATTern:%s:%s:LENGth?" % (self.mod_type, pat_type)
            )

        return message

    def set_pattern_length(self, type, length):
        self.api_set_module(7)
        time.sleep(0.1)
        if "prts" in type.lower():
            self.connection.write(":SOURce:PATTern:PAM3:PRTS:LENGth %s" % length)
        else:
            self.connection.write(":SOURce:PATTern:PAM4:PRBS:LENGth %s" % length)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_pattern(self, pat_type, length):
        # pay attention - double check modulation, pattern and length connections
        # Example {"PAM3"}, {"PRBS"}, {7|9|10|11|13|15|19|20|23|31}
        # Example {"PAM3"}, {"PRTS"}, {7|19}
        self.api_set_module(7)
        time.sleep(0.1)

        # if not mod_type == self.get_modulation_type():
        #     self.set_modulation_type(self.mod_type), time.sleep(2)
        # mod_type = "NRZ"
        if self.mod_type == "NRZ":
            self.connection.write(":SOURce:PATTern:%s:LENGth %s" % (pat_type, length))
        else:
            self.connection.write(
                ":SOURce:PATTern:PAM3:%s:LENGth %s" % (pat_type, length)
            )
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_pattern_prbs_invert(self):
        self.set_uentry_id()  # default 1
        time.sleep(0.1)
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface()  # default 1
        time.sleep(0.1)
        message = self.connection.query(":SOURce:PATTern:LOGic?")
        return message

    def set_pattern_prbs_invert(self):
        self.set_uentry_id()  # default 1
        time.sleep(0.1)
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface()  # default 1
        time.sleep(0.1)
        pos_neg = self.get_pattern_prbs_invert()
        pos_neg = "NEG" if "pos" in pos_neg.lower() else "POS"
        self.connection.write(":SOURce:PATTern:LOGic %s" % (pos_neg))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_pattern_prbs_logic(self, logic="POS"):
        self.set_uentry_id()  # default 1
        time.sleep(0.1)
        self.api_set_module(7)
        time.sleep(0.1)
        self.set_interface()  # default 1
        time.sleep(0.1)
        self.connection.write(":SOURce:PATTern:LOGic %s" % (logic))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    # MODULE 4
    def get_rj_state(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:RJ:ENABle?")
        ## Example : {"1", "0"}
        return message

    def set_rj_state(self, state, jbert="nul"):
        # Example : state = {"OFF"/0}, {"ON"/1}
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:RJ:ENABle " + str(state))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_rj_amp(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:RJ:AMPLitude?")
        return message

    def set_rj_amp(self, rj_amp, jbert="null"):
        # Example : rj_amp = {from 0 to 0.500}
        # !!! some rj_amp values can't be applied check twice if sent value applied !!!
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:RJ:AMPLitude " + str(rj_amp))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_sj_state(self, sj_type="SJ"):
        # Example : sj_type = {SJ/SJ1 | SJ2}
        if sj_type == "SJ1":
            sj_type = "SJ"
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:%s:ENABle? " % sj_type)
        return message

    def set_glitch_free_state(self, state):
        # Example : state = {ON/OFF}
        self.api_set_module(7)
        time.sleep(0.1)
        self.connection.write(":OUTPut:DATA:GFRee %s" % state)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_sj_state(self, sj_type, state):
        # Example : sj_type = {SJ/SJ1|SJ2} | state = {"OFF"|0} or {"ON"|1}
        if sj_type == "SJ1":
            sj_type = "SJ"
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:%s:ENABle " % sj_type + str(state))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_cm_state(self, state):
        # Example : state = {"OFF"|0} or {"ON"|1}
        self.api_set_module(8)
        time.sleep(0.1)
        self.connection.write(":SOURce:CMNoise:ENABle %s" % str(state))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_dm_state(self, state):
        # Example : state = {"OFF"|0} or {"ON"|1}
        self.api_set_module(8)
        time.sleep(0.1)
        self.connection.write(":SOURce:DMNoise:ENABle %s" % str(state))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_dm_state(self, state):
        # Example : state = {"OFF"|0} or {"ON"|1}
        self.api_set_module(8)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:DMNoise:ENABle?" % str(state))
        time.sleep(0.1)
        return message

    def set_dm_freq(self, state):
        # amp : 2 - 10 (float)
        self.api_set_module(8)
        time.sleep(0.1)
        self.connection.write(":SOURce:DMNoise:FREQuency %s" % str(state))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_dm_freq(self):
        # amp : 2 - 10 (float)
        self.api_set_module(8)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:DMNoise:FREQuency?")
        time.sleep(0.1)
        return message

    def set_dm_amp(self, amp):
        # amp : 0 - 200 (float)
        self.api_set_module(8)
        time.sleep(0.1)
        self.connection.write(":SOURce:DMNoise:AMPLitude %s" % str(amp))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_dm_amp(self):
        # amp : 0 - 200 (float)
        self.api_set_module(8)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:DMNoise:AMPLitude?")
        time.sleep(0.1)
        return message

    def get_sj_amp(self, sj_type="SJ"):
        # Example : sj_type = {SJ/SJ1 | SJ2}
        if sj_type == "SJ1":
            sj_type = "SJ"
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:%s:AMPLitude? " % sj_type)
        return message

    def set_sj_amp(self, sj_type, value):
        # Example : sj_type = {SJ/SJ1|SJ2} | value = {0 to 2000.000 UI}
        # !!! some sj_amp values can't be applied check twice if sent value applied !!!
        if sj_type == "SJ1":
            sj_type = "SJ"
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:%s:AMPLitude " % sj_type + str(value))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_sj_freq(self, sj_type="SJ"):
        # Example : sj_type = {SJ/SJ1 | SJ2}
        if sj_type == "SJ1":
            sj_type = "SJ"
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:%s:FREQuency? " % sj_type)
        return message

    def set_sj_freq(self, sj_type, value):
        # Example : sj_type = {SJ/SJ1|SJ2} | value = {10 to 250,000,000 Hz}
        # !!! some sj_freq values can't be applied check twice if sent value applied !!!
        if sj_type == "SJ1":
            sj_type = "SJ"
        self.api_set_module(4)
        time.sleep(0.1)
        mes = ":SOURce:JITTer:%s:AMPLitude " % sj_type + str(value)
        self.connection.write(":SOURce:JITTer:%s:FREQuency " % sj_type + str(value))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ssc_state(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:SSC:ENABle?")
        return message

    def set_ssc_state(self, state):
        # Example : state = {"OFF"|0} or {"ON"|1}
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:ENABle " + str(state))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ssc_profile(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:SSC:PROFile?")
        return message

    def set_ssc_profile(self, ssc_profile_type="TRIangular"):
        # Example : ssc_profile_type = {TRIangular | USB4 | VARiable }
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:PROFile " + ssc_profile_type)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ssc_type(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:SSC:TYPE?")
        return message

    def set_ssc_type(self, ssc_type="DOWN"):
        # Example : ssc_type = {DOWN | CENTer | UP}
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:TYPE " + ssc_type)
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ssc_freq(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:SSC:FREQuency?")
        return message

    def set_ssc_freq(self, value):
        # Example : value = {28000 to 37000 Hz}
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:FREQuency " + str(value))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ssc_deviation(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:JITTer:SSC:DEViation?")
        return message

    def set_ssc_deviation(self, value):
        # Example : value = {0 to 7000ppm / 1ppm Step}
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:DEViation " + str(value))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_ssc_deviation_offset(self):
        self.api_set_module(4)
        time.sleep(0.1)
        message = self.connection.query(":OUTPut:CLOCk:OFFSet:PPM?")
        return message

    def set_ssc_deviation_offset(self, value):
        # Example : value = {-1,000 to +1,000ppm / 1ppm Step}
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":OUTPut:CLOCk:OFFSet:PPM " + str(value))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_ssc_start(self):
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:STARt")
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_ssc_stop(self):
        self.api_set_module(4)
        time.sleep(0.1)
        self.connection.write(":SOURce:JITTer:SSC:STOP")
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_WN_Amplitude(self, Amplitude):
        self.api_set_module(8)
        time.sleep(0.1)
        self.connection.write(":SOURce:WHNoise:AMPLitude " + str(Amplitude))
        time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_CM_Amplitude(self, Amplitude):
        self.api_set_module(8)
        time.sleep(0.1)
        self.connection.write(":SOURce:CMNoise:AMPLitude " + str(Amplitude))
        # time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def get_cm_amp(self):
        self.api_set_module(8)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:CMNoise:AMPLitude?")
        return message

    def set_CM(self, amp, freq):
        # amp is from 2 - 250 (mVpp)
        # freq in MHz 100MHz - 1000MHz LOW BAND,
        #             1000MHz - 6000MHz HIGH BAND
        self.api_set_module(8)
        time.sleep(0.1)
        # first update frequency BAND -> 100MHz - 1000MHz LOW, 1GHz - 6GHz HIGH
        freq_band = "HIGH" if freq * 1e-6 >= 1000 else "LOW"
        self.connection.write(":SOURce:CMNoise:BAND %s" % freq_band)
        val = int(freq * 1e-6) if freq_band == "LOW" else float(freq * 1e-6 / 1000)
        self.connection.write(":SOURce:CMNoise:FREQuency %s" % str(val))
        print("setting CM noise to Freq=%sMHz" % (freq * 1e-6))
        # set amplitude 0 - 250 mVpp
        self.connection.write(":SOURce:CMNoise:AMPLitude %s" % str(amp))
        time.sleep(3)
        # time.sleep(0.1)
        self.operationStatus = "set"
        return self.operationStatus

    def set_CM_freq(self, freq=400000000):
        self.api_set_module(8)
        time.sleep(0.1)
        freq_band = "HIGH" if freq * 1e-6 >= 1000 else "LOW"
        self.connection.write(":SOURce:CMNoise:BAND %s" % freq_band)
        val = int(freq * 1e-6) if freq_band == "LOW" else float(freq * 1e-6 / 1000)
        self.connection.write(":SOURce:CMNoise:FREQuency %s" % str(val))
        print("setting CM noise to Freq=%sMHz" % (freq * 1e-6))

    def get_CM_freq(self):
        self.api_set_module(8)
        time.sleep(0.1)
        message = self.connection.query(":SOURce:CMNoise:FREQuency?")
        return message

    # !!!
    def save_config(self, config_file):
        if self._type == "bert_anritsu_mp1800":
            self.set_unit(1)
            time.sleep(0.1)
            self.api_set_module(6)
            time.sleep(0.1)
        # message = ':SOURce:JITTer:SSC:DEViation ' + str(deviation)
        # self.connection.write(message)
        elif self._type == "bert_anritsu_mp1900":
            message = ":SYSTem:MMEMory:QSTore " + '"' + config_file + '",""'
            self.connection.write(message)
            time.sleep(15)
        self.operationStatus = "set"
        return self.operationStatus
