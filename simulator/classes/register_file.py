class RegisterFile():
    reg = {
        0: ["zero", 0, False],
        2: ["v0", 0, False],
        3: ["v1", 0, False],
        4: ["a0", 0, False],
        5: ["a1", 0, False],
        6: ["a2", 0, False],
        7: ["a3", 0, False],
        8: ["t0", 0, False],
        9: ["t1", 0, False],
        10: ["t2", 0, False],
        11: ["t3", 0, False],
        12: ["t4", 0, False],
        13: ["t5", 0, False],
        14: ["t6", 0, False],
        15: ["t7", 0, False],
        16: ["s0", 0, False],
        17: ["s1", 0, False],
        18: ["s2", 0, False],
        19: ["s3", 0, False],
        20: ["s4", 0, False],
        21: ["s5", 0, False],
        22: ["s6", 0, False],
        23: ["s7", 0, False],
        24: ["t8", 0, False],
        25: ["t9", 0, False],
        29: ["sp", 0, False],
        31: ["ra", 0, False],
        32: ["hi", 0, False],
        33: ["lo", 0, False]
    }


    def write(self, register_number, value):
        """
        Write a value to the register update queue.
        :param register_number: register number to update.
        :param value: value to update register with.
        """
        if register_number == 0: # Cannot write to zero'th register
            return
        self.reg[register_number][1] = value # Update register value in queue
        self.reg[register_number][2] = True # Mark as dirty


    def commit(self, register_file):
        """
        Commit the changes of the queue into the main register_file.
        :param register_file: register file to commit changes to.
        """
        for register, contents in self.reg.items():
            if contents[2]:
                register_file[register][1] = contents[1]
