
import serial

SCASS_CMD_HELLOWORLD            = 'H'.encode("ascii")
SCASS_CMD_INIT_EXPERIMENT       = 'I'.encode("ascii")
SCASS_CMD_RUN_EXPERIMENT        = 'R'.encode("ascii")
SCASS_CMD_EXPERIMENT_NAME       = 'N'.encode("ascii")
SCASS_CMD_GOTO                  = 'G'.encode("ascii")
SCASS_CMD_GET_CYCLES            = 'C'.encode("ascii")
SCASS_CMD_GET_INSTRRET          = 'E'.encode("ascii")
SCASS_RSP_OKAY                  = '0'.encode("ascii")
SCASS_RSP_ERROR                 = '!'.encode("ascii")
SCASS_CMD_GET_VAR_NUM           = 'V'.encode("ascii")
SCASS_CMD_GET_VAR_INFO          = 'D'.encode("ascii")
SCASS_CMD_GET_VAR_VALUE         = '1'.encode("ascii")
SCASS_CMD_SET_VAR_VALUE         = '2'.encode("ascii")
SCASS_CMD_RAND_GET_LEN          = 'L'.encode("ascii")
SCASS_CMD_RAND_SEED             = 'S'.encode("ascii")

SCASS_FLAG_RANDOMISE            = (0x1 << 0)
SCASS_FLAG_INPUT                = (0x1 << 1)
SCASS_FLAG_OUTPUT               = (0x1 << 2)
SCASS_FLAG_TTEST_VAR            = (0x1 << 3)

class Target(object):
    """
    The communications bridge between the target device and the
    host PC.
    """

    def __init__(self, port, baud):
        """
        Create and open a new connection to a target device.
        """
        assert type(port) is str, "Serial port name must be a string"
        assert type(baud) is int, "Serial baud rate must be an integer"

        self.port           = serial.Serial()
        self.port.baudrate  = baud
        self.port.port      = port
        self.port.timeout   = 3
        
        self.port.open()

        self.port.reset_input_buffer()
        self.port.reset_output_buffer()

        self.exception_on_command_fail = True
        self.port.read()


    def doInitExperiment(self):
        """Do any one-time experiment initialisation needed"""
        self.__sendByte(SCASS_CMD_INIT_EXPERIMENT)
        return self.__cmdSuccess()


    def doRunExperiment(self):
        """Run the experiment once"""
        self.__sendByte(SCASS_CMD_RUN_EXPERIMENT)
        return self.__cmdSuccess()


    def doGetExperiementName(self):
        """Return the name of the experiment currently running as a string
        if successful, otherwise return False"""
        self.__sendByte(SCASS_CMD_EXPERIMENT_NAME)
        slen = int.from_bytes(self.__recvByte(),byteorder="little")

        ename = ""
        for i in range(0, slen):
            ename += (str(self.__recvByte(),encoding="ascii"))

        if(self.__cmdSuccess()):
            return ename
        else:
            return False


    def doGetExperimentCycles(self):
        """Return the number of cycles it takes to execute 1 experiment.
        You need to have run the experiment atleast once for this to work."""
        self.__sendByte(SCASS_CMD_GET_CYCLES)
        
        bdata  = self.port.read(4)
        assert(len(bdata) == 4), "Expected 4 bytes, got %d"%len(bdata)
        result = int.from_bytes(bdata,byteorder="big")

        if(self.__cmdSuccess()):
            return result
        else:
            return False


    def doGetExperimentInstrRet(self):
        """Return the number instructions executeed by 1 experiment run.
        You need to have run the experiment atleast once for this to work."""
        self.__sendByte(SCASS_CMD_GET_INSTRRET)
        
        bdata  = self.port.read(4)
        assert(len(bdata) == 4), "Expected 4 bytes, got %d"%len(bdata)
        result = int.from_bytes(bdata,byteorder="big")

        if(self.__cmdSuccess()):
            return result
        else:
            return False


    def doGoto(self, address):
        """
        Issue a goto command to the target, causing it to jump immediately
        to the supplied memory address.

        The target does not issue a return code, hence this function always
        returns True.

        :param address:
            A 4 byte array containing the memory address to jump too.  The
            address should observe *little endian* byte ordering.
        """

        self.__sendByte(SCASS_CMD_GOTO)

        self.port.write(address)

        return True


    def doGetVarNum(self):
        """
        Return the number of variables on the target which can be
        managed by the SCASS framework. Number will be between 0 and 255.

        :rtype: int or False if the command succeeds or fails respectivley.
        """

        self.__sendByte(SCASS_CMD_GET_VAR_NUM)
        
        bdata = self.port.read(1)
        result= int.from_bytes(bdata,byteorder="big")

        if(self.__cmdSuccess()):
            return result
        else:
            return False


    def doGetVarInfo(self, varnum):
        """
        Return a tuple which describes a single variable under management
        on the target device or False if the requested variable was
        out of range.
        
        :param varnum: Index of the variable to get information for.

        :rtype: tuple of the form:
            (name, variable size, variable flags)
        """

        self.__sendByte(SCASS_CMD_GET_VAR_INFO)
        self.__sendByte(bytes([varnum])[0])
        
        namelen = int.from_bytes(self.port.read(4),byteorder="big")
        varsize = int.from_bytes(self.port.read(4),byteorder="big")
        flags   = int.from_bytes(self.port.read(4),byteorder="big")
        name    = str(self.port.read(namelen),encoding="ascii")

        if(self.__cmdSuccess()):
            return (name, varsize, flags)
        else:
            return False


    def doGetVarValue(self, varnum, length):
        """
        Get the current value of the specified variable.

        :param varnum: The index of the variable.
        :param length: Number of bytes to read. Found using doGetVarInfo

        :rtype: bytes or False
        """
        
        self.__sendByte(SCASS_CMD_GET_VAR_VALUE)
        self.__sendByte(bytes([varnum])[0])

        rdata = self.port.read(length)

        if(self.__cmdSuccess()):
            return rdata
        else:
            return False


    def doSetVarValue(self, varnum, data):
        """
        Get the current value of the specified variable.

        :param varnum: The index of the variable.
        :param data: The data to send. Assumed to be the correct length.

        :rtype: bool
        """
        
        self.__sendByte(SCASS_CMD_SET_VAR_VALUE)
        self.__sendByte(bytes([varnum])[0])
        self.port.write(data)

        if(self.__cmdSuccess()):
            return True 
        else:
            return False


    def doRandGetLen(self):
        """
        Get the length of the on-board randomness array.

        :rtype: int or False
        """

        self.__sendByte(SCASS_CMD_RAND_GET_LEN)

        bdata = self.port.read(4)
        result= int.from_bytes(bdata,byteorder="big")

        if(self.__cmdSuccess()):
            return result
        else:
            return False


    def doRandSeed(self, data):
        """
        Seed the onboard randomness array with the supplied data.
        Assumes that the supplied data bytes are of length "doRandGetLen"

        :rtype: bool
        """
        self.__sendByte(SCASS_CMD_RAND_SEED)

        self.port.write(data)

        if(self.__cmdSuccess()):
            return result
        else:
            return False


    def doHelloWorld(self):
        """
        Run a hello world test of communications.
        Return True if everything worked. False otherwise.
        """
        self.__sendByte(SCASS_CMD_HELLOWORLD)
        return self.__cmdSuccess()


    def __sendByte(self, b):
        #print("> %s"%(str(b)))
        self.port.write(b)
        self.port.flush()


    def __recvByte(self):
        rsp = self.port.read()
        #print("< %s"%str(rsp))
        return rsp


    def __getRsp(self):
        """Get the response code from the target"""
        return self.__recvByte()


    def __cmdSuccess(self):
        """Return true if the next byte read is SCASS_RSP_OKAY, else
            return false"""
        rsp_code = self.__getRsp()
        if(rsp_code == SCASS_RSP_OKAY):
            return True
        elif(rsp_code == SCASS_RSP_ERROR):
            bad_cmd = self.port.read()
            if(self.exception_on_command_fail):
                raise Exception("Failed SCASS code: %s" %str(bad_cmd))
            return False
        else:
            if(self.exception_on_command_fail):
                raise Exception("Unknown SCASS code: %s" %str(rsp_code))
            return False

