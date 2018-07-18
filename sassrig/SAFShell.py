
import os
import sys
import cmd
import shlex
import serial

from .SassComms             import SassComms
from .SassScope             import SassScope
from .SAFTTestCapture       import SAFTTestCapture
from .SAFTTestEvaluation    import SAFTTestEvaluation

class scolors:
    SBOLD       = '\033[1m'
    SENDC       = '\033[0m'
    SFAIL       = '\033[91m'
    SHEADER     = '\033[95m'
    SOKBLUE     = '\033[94m'
    SOKGREEN    = '\033[92m'
    SUNDERLINE  = '\033[4m'
    SWARNING    = '\033[93m'


def normal_filepath(p):
    return os.path.abspath(os.path.expandvars(os.path.expanduser(p)))


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
        self.scope      = None
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

    def __check_scope(self):
        """
        Check if we have a currently open connection to as oscilisciope

        :rtype: bool
        :return: True if a connection is open, False otherwise
        """
        if(self.scope == None):
            return False
        else:
            return True


    def emptyline(self):
        """
        Override default behaviour. Does nothing if the prompt gets an
        empty line as input.
        """
        pass


    def do_scope_open(self, args):
        """
        Connect to the scope
        """
        
        if(self.__check_scope()):

            print("Already connected to a scope. Disconnect before opening")

        else:
            
            print("Opening scope connection...")
            self.scope = SassScope()
            self.scope.OpenScope()
        
            self.scope.sample_count    = 12500
            self.scope.sample_frequency= 125e6
            self.scope.sample_range    = 20e-3

            self.scope.ConfigureScope()

            print("Opened scope connection")
            print("\tSample count: %d" % self.scope.sample_count)
            print("\tSample freq : %f" % self.scope.sample_frequency)
            print("\tSample range: %f" % self.scope.sample_range)


    def do_scope_close(self, args):
        """
        Disconnect from the currently connected scope.
        """
        if(self.__check_scope()):
            self.scope.CloseScope()
            self.scope = None
            print("Closed scope connection")
        else:
            print("No scope connection to close")


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


    def do_capture_ttest(self, args):
        """
        Capture two sets of traces to be used for a ttest.

        Expects three arguments:
        - num_traces
        - set1_tracefile
        - set2_tracefile
        """
        args = shlex.split(args)
        if(len(args) != 3):
            print("capture_ttest expects 3 arguments")
            return

        numtraces, set1_file, set2_file = args
        set1_file = normal_filepath(set1_file)
        set2_file = normal_filepath(set2_file)
        numtraces = int(numtraces)

        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        elif(self.__check_scope() == False):

            print("No active oscilliscipe connection.")

        else:
            
            print("Capturing ttest trace sets...")
            
            cap = SAFTTestCapture(self.comms,self.scope,num_traces=numtraces)

            print("Trace sets key: %s" % cap.key.hex())
            print("Set1 Message: %s" % cap.set1_msg.hex())
            
            cap.RunCapture()

            print("Captured %d traces." % cap.TotalTraces())
            print("\tSet1 Size: %d" % len(cap.set1))
            print("\tSet2 Size: %d" % len(cap.set2))

            print("Writing %s" % set1_file)
            cap.set1.DumpTRS(set1_file)

            print("Writing %s" % set2_file)
            cap.set2.DumpTRS(set2_file)

            del cap
            print("TTest Capture Finished")


    def do_evaluate_ttest(self, args):
        """
        Run a t-test on pre-captured trace sets.
        
        Arguments:
        set1    - Filepath of first trace set with all the same message
        set2    - Filepath of second trace set with uniform random message
        figpath - Filepath to write the graph of traces too.
        """
        args = shlex.split(args)
        if(not len(args) in [2,3]):
    
            print("evaluate_ttest expects two or three arguments!")
            print(" Got %s" % str(args))

        else:
            set1 = args[0]
            set2 = args[1]
            figpath = None
            if(len(args) == 3):
                figpath = args[2]
        
            set1    = normal_filepath(set1)
            set2    = normal_filepath(set2)
            figpath = normal_filepath(figpath)
            
            ev      = SAFTTestEvaluation(set1,set2)

            print("Evaluating TTest:")
            print("\tSet 1: %s" % set1)
            print("\tSet 2: %s" % set2)
            print("\tConfidence Value: %f" % ev.confidence)

            result  = ev.Evaluate()

            if(result):
                print(scolors.SOKGREEN+"TTest passed"+scolors.SENDC)
            else:
                print(scolors.SFAIL+"TTest failed"+scolors.SENDC)

            if(figpath != None):
                print("Saving graphs to %s" % figpath)
                fig = ev.make_graph()
                fig.savefig(figpath)


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

