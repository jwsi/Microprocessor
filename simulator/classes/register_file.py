class RegisterFile():
    reg = {
        0: ["zero", 0, False],
        8: ["t0", 0, False],
        9: ["t1", 0, False],
        10: ["t2", 0, False],
        11: ["t3", 0, False],
        12: ["t4", 0, False],
        13: ["t5", 0, False],
        14: ["t6", 0, False],
        15: ["t7", 0, False],
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
