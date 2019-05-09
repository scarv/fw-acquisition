
import serial

SCASS_CMD_HELLOWORLD      = "H".encode("ascii")
SCASS_CMD_INIT_EXPERIMENT = "I".encode("ascii")
SCASS_CMD_RUN_EXPERIMENT  = "R".encode("ascii")
SCASS_CMD_SEED_PRNG       = "P".encode("ascii")
SCASS_RSP_OKAY            = "0".encode("ascii")
SCASS_RSP_ERROR           = "!".encode("ascii")

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

    def doSeedPRNG(self, seed):
        """
        Set the PRNG seed value, where the supplied seed is an
        integer
        """
        assert(isinstance(seed,int))

        self.__sendByte(SCASS_CMD_SEED_PRNG)

        self.__sendByte((seed >> 24) & 0xFF)
        self.__sendByte((seed >> 16) & 0xFF)
        self.__sendByte((seed >>  8) & 0xFF)
        self.__sendByte((seed >>  0) & 0xFF)

        return self.__cmdSuccess()


    def doHelloWorld(self):
        """
        Run a hello world test of communications.
        Return True if everything worked. False otherwise.
        """
        self.__sendByte(SCASS_CMD_HELLOWORLD)
        return self.__cmdSuccess()


    def __sendByte(self, b):
        #print("> %s"%str(b))
        self.port.write(b)
        self.port.flush()

    def __getRsp(self):
        """Get the response code from the target"""
        rsp = self.port.read()
        #print("< %s"%str(rsp))
        return rsp   

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
