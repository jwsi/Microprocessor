class RegisterFile():
    def __init__(self):
        """
        Constructor for the Register File class.
        """
        self.reg = {
            # Register_Number : [NAME, VALUE, VALID, ROB_ENTRY]
            0:  {"name" : "zero", "value" : 0, "valid" : True, "rob_entry" : None},
            1:  {"name" : "at", "value" : 0, "valid" : True, "rob_entry" : None},
            2:  {"name" : "v0", "value" : 0, "valid" : True, "rob_entry" : None},
            3:  {"name" : "v1", "value" : 0, "valid" : True, "rob_entry" : None},
            4:  {"name" : "a0", "value" : 0, "valid" : True, "rob_entry" : None},
            5:  {"name" : "a1", "value" : 0, "valid" : True, "rob_entry" : None},
            6:  {"name" : "a2", "value" : 0, "valid" : True, "rob_entry" : None},
            7:  {"name" : "a3", "value" : 0, "valid" : True, "rob_entry" : None},
            8:  {"name" : "t0", "value" : 0, "valid" : True, "rob_entry" : None},
            9:  {"name" : "t1", "value" : 0, "valid" : True, "rob_entry" : None},
            10: {"name" : "t2", "value" : 0, "valid" : True, "rob_entry" : None},
            11: {"name" : "t3", "value" : 0, "valid" : True, "rob_entry" : None},
            12: {"name" : "t4", "value" : 0, "valid" : True, "rob_entry" : None},
            13: {"name" : "t5", "value" : 0, "valid" : True, "rob_entry" : None},
            14: {"name" : "t6", "value" : 0, "valid" : True, "rob_entry" : None},
            15: {"name" : "t7", "value" : 0, "valid" : True, "rob_entry" : None},
            16: {"name" : "s0", "value" : 0, "valid" : True, "rob_entry" : None},
            17: {"name" : "s1", "value" : 0, "valid" : True, "rob_entry" : None},
            18: {"name" : "s2", "value" : 0, "valid" : True, "rob_entry" : None},
            19: {"name" : "s3", "value" : 0, "valid" : True, "rob_entry" : None},
            20: {"name" : "s4", "value" : 0, "valid" : True, "rob_entry" : None},
            21: {"name" : "s5", "value" : 0, "valid" : True, "rob_entry" : None},
            22: {"name" : "s6", "value" : 0, "valid" : True, "rob_entry" : None},
            23: {"name" : "s7", "value" : 0, "valid" : True, "rob_entry" : None},
            24: {"name" : "t8", "value" : 0, "valid" : True, "rob_entry" : None},
            25: {"name" : "t9", "value" : 0, "valid" : True, "rob_entry" : None},
            26: {"name" : "k0", "value" : 0, "valid" : True, "rob_entry" : None},
            27: {"name" : "k1", "value" : 0, "valid" : True, "rob_entry" : None},
            28: {"name" : "gp", "value" : 0, "valid" : True, "rob_entry" : None},
            29: {"name" : "sp", "value" : 0, "valid" : True, "rob_entry" : None},
            30: {"name" : "fp", "value" : 0, "valid" : True, "rob_entry" : None},
            31: {"name" : "ra", "value" : 0, "valid" : True, "rob_entry" : None},
            32: {"name" : "hi", "value" : 0, "valid" : True, "rob_entry" : None},
            33: {"name" : "lo", "value" : 0, "valid" : True, "rob_entry" : None}
        }


    def write(self, rob_instruction, rob):
        """
        Write a finished ROB item back to the register file.
        :param rob_instruction: register number to update.
        :param rob: re-order buffer to use.
        :param stdscr: terminal to writeback to.
        :return: List of registers written to.
        """
        written_to = []
        for register, value in rob_instruction["result"].items():
            if register == 0: # Cannot write to zero'th register
                continue
            self.reg[register]["value"] = value
            if self.reg[register]["rob_entry"] == rob_instruction["instruction"].rob_entry:
                self.reg[register]["valid"] = True
            written_to.append(register)
        rob.mark_written(rob_instruction["instruction"].rob_entry)
        return written_to


    def set_all_valid(self):
        """
        Sets all registers in register file to be valid.
        This is useful in a branch prediction failure.
        """
        for key in self.reg.keys():
            self.reg[key]["valid"] = True


    def no_writebacks(self):
        """
        Checks that there are no pending writebacks to the main register file.
        :return: Boolean representing pending writeback status.
        """
        for reg in self.reg:
            if not self.reg[reg]["valid"]:
                return False
        return True


    def get_value(self, register):
        """
        Returns the value located in the register one wishes to lookup.
        If the register is not valid a ROB entry id is returned instead.
        :param register: The register to access.
        :return: Boolean representing whether the register is valid,
        and a value representing the raw value or the ROB entry id.
        """
        if self.reg[register]["valid"]:
            return True, self.reg[register]["value"]
        return False, self.reg[register]["rob_entry"]


    def invalidate_register(self, register, rob_entry):
        """
        Invalidates a register and updates the rob_entry.
        :param register: Register to invalidate.
        :param rob_entry: ROB entry to link to.
        """
        if register == 0:
            return
        self.reg[register]["valid"] = False
        self.reg[register]["rob_entry"] = rob_entry
