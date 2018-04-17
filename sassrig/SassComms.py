
"""
This file contains the utilities needed to communicate with the target
platform.
"""

import os
import sys
import time
import logging as log

import serial

#
# Command codes for communicating with the target
#
SASS_CMD_HELLOWORLD = b"\x01"
SASS_CMD_SET_KEY    = b"\x02"
SASS_CMD_GET_KEY    = b"\x03"
SASS_CMD_SET_MSG    = b"\x04"
SASS_CMD_GET_MSG    = b"\x05"
SASS_CMD_SET_CIPHER = b"\x06"
SASS_CMD_GET_CIPHER = b"\x07"
SASS_CMD_SET_CFG    = b"\x08"
SASS_CMD_GET_CFG    = b"\x09"
SASS_CMD_DO_ENCRYPT = b"\x0A"
SASS_CMD_DO_DECRYPT = b"\x0B"

#
# Status codes for checking if commands all worked.
#
SASS_STATUS_OK      = b"\xA0"
SASS_STATUS_ERR     = b"\xFA"

class SassComms:
    """
    This class is responsible for implementing the communication protocol
    between the target platform and the testing flow.
    """


    def __init__(self,
                 serialPort = "/dev/ttyUSB1",
                 serialBaud = 19200):
        """
        Create and open a new serial port connection according to the
        supplied arguments.
        """
        assert type(serialBaud) is int, "Serial baud rate must be an integer"
        assert type(serialPort) is str, "Serial port name must be a string"

        self.keylength      = 16
        self.msglength      = 16
        self.cfglength      = 1
        
        self.port           = serial.Serial()

        self.port.baudrate  = serialBaud
        self.port.port      = serialPort
        self.port.timeout   = 3

        log.info("Opening serial port %s with baud %d" % (
            self.port.port, self.port.baudrate))

        self.port.open()

        if(self.port.is_open):
            log.info("Port opened successfully")
        else:
            log.error("Failed to open port!")
            sys.exit(1)


    def __GetResponse__(self):

        response = self.port.read()

        if(len(response) == 0):
            log.error("Port timeout waiting for a response")
            sys.exit(1)

        if(response == SASS_STATUS_OK):
            log.info("SASS_STATUS_OK")
            return True
        elif(response == SASS_STATUS_ERR):
            log.info("SASS_STATUS_ERR")
            return False
        else:
            log.error("Unknown response code:")
            log.error(response)
            sys.exit(1)


    def doHelloWorld(self):
        """
        A test command which checks the command response protocol works.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """

        log.info("SASS_CMD_HELLOWORLD")

        self.port.write(SASS_CMD_HELLOWORLD)
        self.port.flush()

        return self.__GetResponse__()


    def doSetKey(self, new_key):
        """
        Tell the target to update its key store with the new key.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """
        assert len(new_key) == self.keylength

        log.info("SASS_CMD_SET_KEY %s" % new_key.hex())
        
        hp = int(self.msglength/2)

        self.port.write(SASS_CMD_SET_KEY)
        self.port.write(new_key[:hp])
        self.port.flush()
        time.sleep(0.1)
        self.port.write(new_key[hp:])
        self.port.flush()
        
        return self.__GetResponse__()


    def doGetKey(self):
        """
        Tell the target to echo back its current key value.
        - Return the key if all is okay.
        - Return False if we get an error response code.
        """

        log.info("SASS_CMD_GET_KEY")

        self.port.write(SASS_CMD_GET_KEY)
        self.port.flush()

        key = self.port.read(self.keylength)
        rsp = self.__GetResponse__()

        if(rsp):
            return key
        else:
            return rsp


    def doSetMsg(self, new_msg):
        """
        Tell the target to update its msg store with the new msg.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """
        assert len(new_msg) == self.msglength

        log.info("SASS_CMD_SET_MSG %s" % new_msg.hex())

        hp = int(self.msglength/2)

        self.port.write(SASS_CMD_SET_MSG)
        self.port.write(new_msg[:hp])
        self.port.flush()
        time.sleep(0.1)
        self.port.write(new_msg[hp:])
        self.port.flush()
        
        return self.__GetResponse__()


    def doGetMsg(self):
        """
        Tell the target to echo back its current msg value.
        - Return the msg if all is okay.
        - Return False if we get an error response code.
        """

        log.info("SASS_CMD_GET_MSG")

        self.port.write(SASS_CMD_GET_MSG)
        self.port.flush()

        msg = self.port.read(self.msglength)
        rsp = self.__GetResponse__()

        if(rsp):
            return msg
        else:
            return rsp


    def doSetCipher(self, new_cipher):
        """
        Tell the target to update its cipher store with the new cipher.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """

        log.info("SASS_CMD_SET_CIPHER %s" % new_cipher.hex)

        self.port.write(SASS_CMD_SET_CIPHER)
        self.port.write(new_cipher)
        self.port.flush()
        
        return self.__GetResponse__()


    def doGetCipher(self):
        """
        Tell the target to echo back its current cipher value.
        - Return the cipher if all is okay.
        - Return False if we get an error response code.
        """

        log.info("SASS_CMD_GET_CIPHER")

        self.port.write(SASS_CMD_GET_CIPHER)
        self.port.flush()

        cipher = self.port.read(self.cipherlength)
        rsp = self.__GetResponse__()

        if(rsp):
            return cipher
        else:
            return rsp


    def doSetCfg(self, field, value):
        """
        Tell the target to update its config store with the new value.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """

        log.info("SASS_CMD_SET_CFG %s" % new_cfg.hex)

        self.port.write(SASS_CMD_SET_CFG)
        self.port.write(field)
        self.port.write(value)
        self.port.flush()
        
        return self.__GetResponse__()


    def doGetCfg(self,field):
        """
        Tell the target to echo back its current config value.
        - Return the config field value if all is okay.
        - Return False if we get an error response code.
        """

        log.info("SASS_CMD_GET_CFG")

        self.port.write(SASS_CMD_GET_CFG)
        self.port.write(field)
        self.port.flush()

        cfg = self.port.read(self.cfglength)
        rsp = self.__GetResponse__()

        if(rsp):
            return cfg
        else:
            return rsp


    def doEncrypt(self):
        """
        Given the current message and key on the target, create a
        cipher text on the target.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """

        log.info("SASS_CMD_DO_ENCRYPT")

        self.port.write(SASS_CMD_DO_ENCRYPT)
        self.port.flush()

        rsp = self.__GetResponse__()

        return rsp

    def doDecrypt(self):
        """
        Given a ciphertext and key on the target, decrypt it and create a
        new message text on the target.
        - Return false if we get an error response.
        - Return true if we get the OK response.
        - Die if we get no response at all or an unexpected response.
        """

        log.info("SASS_CMD_DO_DECRYPT")

        self.port.write(SASS_CMD_DO_ENCRYPT)
        self.port.flush()

        rsp = self.__GetResponse__()
        return rsp


    def ClosePort(self):
        """
        Close the serial port connection
        """

        log.info("Closing serial port %s" % (self.port.port))

        self.port.close()
