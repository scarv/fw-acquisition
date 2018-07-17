
import sys
import cmd
import shlex
import serial

from .SassComms import SassComms

class scolors:
    SBOLD       = '\033[1m'
    SENDC       = '\033[0m'
    SFAIL       = '\033[91m'
    SHEADER     = '\033[95m'
    SOKBLUE     = '\033[94m'
    SOKGREEN    = '\033[92m'
    SUNDERLINE  = '\033[4m'
    SWARNING    = '\033[93m'

class SAFShell(cmd.Cmd):
    """
    A wrapper around the cmd.Cmd class which implements a basic shell for
    running commands around trace acquisitions.
    """

    intro = """
    ================================================
              SCARV Acquisitions Framework
    ================================================
    """
    prompt = scolors.SOKBLUE+"afw> "+scolors.SENDC
    file   = None

    def __init__(self):
        """
        Create and setup a new SAFShell object.
        """
        cmd.Cmd.__init__(self)

        self.comms      = None
        self.exit_shell = False

    def __check_comms(self):
        """
        Check if we have a currently open connection to the target device.

        :rtype: bool
        :return: True if a connection is open, False otherwise
        """
        if(self.comms == None):
            return False
        else:
            return True


    def do_connect(self, args):
        """
        Connect to a target device from which acquisitions will be taken.

        :param str port: The tty/COM port to connect too
        :param int baud: The UART Baud rate of the device
        """
        if(self.__check_comms() == False):

            port, baud = shlex.split(args)
            
            baud = int(baud)
            
            self.comms = SassComms(serialPort = port, serialBaud = baud)
            print("Connected to port %s" % (self.comms.port.port))

            SAFShell.prompt = scolors.SOKGREEN+self.comms.port.port+\
                scolors.SENDC+":"+scolors.SOKBLUE+"afw> "+scolors.SENDC

        else:

            print("Please disconnect the existing port using 'disconnect'")


    def do_connection_info(self,args):
        """
        Print out the current connection information
        """
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        else:

            print("Connection information:")
            print("\tPort: %s" % (self.comms.port.port))
            print("\tBaud: %s" % (self.comms.port.baudrate))


    def do_connection_test(self,args):
        """
        Test that the connection to the target is working.
        """
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        else:

            try:
                if(self.comms.doHelloWorld()):
                    print("Connection is working")
                else:
                    print("Connection test failed")
            except SassCommsException as e:
                print("ERROR: %s" % str(e))
            except serial.SerialTimeoutException:
                print("ERROR: Port response timeout")
                self.do_disconnect()


    def do_encrypt(self, arguments):
        """
        Perform a single encryption round.
        """

        args = shlex.split(arguments)

        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        elif(len(args) == 0):

            rsp = self.comms.doEncrypt()
            if(rsp):
                print("Encryption Successful")
            else:
                print("Encryption Failed")
    
    
    def do_custom_target_cmd(self, arguments):
        """
        Run whatever custom target command has been implemented.
        """

        args = shlex.split(arguments)

        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        elif(len(args) == 0):

            rsp = self.comms.doCustom()
            if(rsp):
                print("Custom command Successful")
            else:
                print("Custom command Failed")


    def do_decrypt(self, arguments):
        """
        Perform a single decryption round.
        """

        args = shlex.split(arguments)

        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        elif(len(args) == 0):

            rsp = self.comms.doDecrypt()
            if(rsp):
                print("Decryption Successful")
            else:
                print("Decryption Failed")


    def do_message_get(self,args):
        """
        Query the target device for the current plaintext
        """
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        else:

            msg = self.comms.doGetMsg()
            print("%s"%msg.hex())


    def do_ciphertext_get(self,args):
        """
        Query the target device for the current ciphertext.
        """
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        else:

            ciphertext = self.comms.doGetCipher()
            print("%s"%ciphertext.hex())


    def do_key_get(self,args):
        """
        Query the target device for the current encryption key.
        """
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        else:

            key = self.comms.doGetKey()
            print("%s"%key.hex())


    def do_disconnect(self, args):
        """
        Disconnect from the current target device.
        """
        if(self.comms != None):
            
            SAFShell.prompt = scolors.SOKBLUE+"afw> "+scolors.SENDC
            
            print("Closing connection to %s" % (self.comms.port.port))

            self.comms.ClosePort()
            self.comms = None

        else:

            print("No connection currently open.")


    def do_exit(self, args):
        """
        Exit the shell session.
        """
        if(self.__check_comms()):
            self.do_disconnect(None)

        self.exit_shell = True
        return True

