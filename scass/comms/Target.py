
import serial

SCASS_CMD_HELLOWORLD            = "H".encode("ascii")
SCASS_CMD_INIT_EXPERIMENT       = "I".encode("ascii")
SCASS_CMD_RUN_EXPERIMENT        = "R".encode("ascii")
SCASS_CMD_SEED_PRNG             = "P".encode("ascii")
SCASS_CMD_EXPERIMENT_NAME       = "N".encode("ascii")
SCASS_CMD_GET_DATA_IN_LEN       = "L".encode("ascii")
SCASS_CMD_GET_DATA_OUT_LEN      = "l".encode("ascii")
SCASS_CMD_GET_DATA_IN           = "D".encode("ascii")
SCASS_CMD_GET_DATA_OUT          = "d".encode("ascii")
SCASS_CMD_SET_DATA_IN           = "W".encode("ascii")
SCASS_CMD_SET_DATA_OUT          = "w".encode("ascii")
SCASS_RSP_OKAY                  = "0".encode("ascii")
SCASS_RSP_ERROR                 = "!".encode("ascii")

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


    def doGetInputDataLength(self):
        """Return the length in bytes of the experiment input data array
        or False if the command fails"""
        self.__sendByte(SCASS_CMD_GET_DATA_IN_LEN)
        
        bdata  = self.port.read(4)
        assert(len(bdata) == 4), "Expected 4 bytes, got %d"%len(bdata)
        result = int.from_bytes(bdata,byteorder="big")

        if(self.__cmdSuccess()):
            return result
        else:
            return False

    def doGetOutputDataLength(self):
        """Return the length in bytes of the experiment output data array
        or False if the command fails"""
        self.__sendByte(SCASS_CMD_GET_DATA_OUT_LEN)
        
        bdata  = self.port.read(4)
        assert(len(bdata) == 4), "Expected 4 bytes, got %d"%len(bdata)
        result = int.from_bytes(bdata,byteorder="big")

        if(self.__cmdSuccess()):
            return result
        else:
            return False


    def doSetInputData(self, data):
        """
        Takes an N length byte array and writes it to the experiment
        input data array on the target side. Does not check the data array
        is the correct length, just writes the whole thing.
        data array should be the same length as value returned by
        doGetExperiementDataLength
        """

        self.__sendByte(SCASS_CMD_SET_DATA_IN)

        self.port.write(data)

        return self.__cmdSuccess()


    def doGetOutputData(self, length):
        """
        Get the contents of the experiment output data array.
        Returns a byte array <length> bytes long. <length> should be
        equal to the value returned by doGetExperiementDataLength
        """

        assert(isinstance(length,int))

        self.__sendByte(SCASS_CMD_GET_DATA_OUT)
        
        tr = self.port.read(length)
        
        assert(len(tr) == length), "Expected %d bytes, got %d"%(
            length,len(tr))
        
        if(self.__cmdSuccess()):
            return tr
        else:
            return False


    def doSetOutputData(self, data):
        """
        Takes an N length byte array and writes it to the experiment
        output data array on the target side. Does not check the data array
        is the correct length, just writes the whole thing.
        data array should be the same length as value returned by
        doGetExperiementDataLength
        """

        self.__sendByte(SCASS_CMD_SET_DATA_OUT)

        self.port.write(data)

        return self.__cmdSuccess()


    def doGetInputData(self, length):
        """
        Get the contents of the experiment input data array.
        Returns a byte array <length> bytes long. <length> should be
        equal to the value returned by doGetExperiementDataLength
        """

        assert(isinstance(length,int))

        self.__sendByte(SCASS_CMD_GET_DATA_IN)
        
        tr = self.port.read(length)
        
        assert(len(tr) == length), "Expected %d bytes, got %d"%(
            length,len(tr))
        
        if(self.__cmdSuccess()):
            return tr
        else:
            return False



    def doSeedPRNG(self, seed):
        """
        Set the PRNG seed value, where the supplied seed is an
        integer
        """
        assert(isinstance(seed,int))

        self.__sendByte(SCASS_CMD_SEED_PRNG)

        ibytes = seed.to_bytes(4,byteorder="little")

        self.port.write(ibytes)

        return self.__cmdSuccess()


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

