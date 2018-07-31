
import os
import sys
import cmd
import shlex
import serial

import pyaes

from tqdm import tqdm

from .SassComms             import SassComms
from .SassComms             import SassCommsException
from .SassScope             import SassScope
from .SAFAttackCPA          import SAFAttackCPA
from .SAFTTestCapture       import SAFTTestCapture
from .SAFTTestEvaluation    import SAFTTestEvaluation
from .SAFTraceWriter        import SAFTraceWriter
from .SAFTraceSet           import SAFTraceSet
from .SassEncryption        import SassEncryption

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

        self.comms          = None
        self.scope          = None
        self.exit_shell     = False
        self.trace_channel  = "A"
        self.trigger_channel= "B"

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


    def do_scope_cfg_trigger(self, args):
        """
        Configure a scope channel as a trigger based on the supplied parameters

        Arguments:
        - Channel: {A,B,C,D}
        - Timeout:  Milliseconds to wait until the trigger aborts
        - Threshold: Value at which the trigger fires.
        - Direction: {Rising, Falling}
        """
        args = shlex.split(args)

        if(len(args) != 4):
            print("scope_cfg_trigger expects 4 arguments! Got %d"%len(args))

        elif(not self.__check_scope()):
            print("No active scope connection. Cannot configure trigger")

        else:
            channel, timeout, threshold, direction = args
            timeout     = int(timeout)
            threshold   = float(threshold)
            self.scope.ConfigureTrigger(channel, threshold, direction, timeout)
            self.trigger_channel = channel
            print("Configured channel %s as a %s trigger with threshold %f" %(
                channel, direction, threshold))


    def do_scope_cfg_channel(self, args):
        """
        Configure a single scope channel based on the supplied parameters.

        Arguments:
        - Channel: {A,B,C,D}
        - Range:
        - Coupling: {DC, AC}
        """
        args = shlex.split(args)

        if(len(args) != 3):
            print("scope_cfg_channel expects 3 arguments! Got %d"%len(args))

        elif(not self.__check_scope()):
            print("No active scope connection. Cannot configure trigger")

        else:
            channel, srange, coupling = args
            srange = float(srange)
            self.scope.ConfigureChannel(channel, srange, coupling)

    def do_scope_cfg_trace_channel(self, args):
        """
        Print or set the scope channel which is extracted and put into
        trace files.
        """
        args = shlex.split(args)

        if(len(args) == 0):
            print(self.trace_channel)
        elif(len(args) == 1):
            self.trace_channel = args[0]
            print("Trace channel is now '%s'" % (self.trace_channel))
        else:
            print("Command expects 0 or 1 arguments. Got %d." % len(args))

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
                self.do_disconnect(None)


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

    def do_set_samples_per_trace(self, args):
        """
        Set the maximum number of samples to record per trace.
        Arguments:
        - int samples - samples per trace to record.
        """

        args = shlex.split(args)
        if(len(args) != 1):
            print("set_samples_per_trace expects 1 argument")
            return

        if(self.__check_scope() == False):

            print("No active oscilliscipe connection.")

        else:

            self.scope.sample_count = int(args[0])
            print("Samples per trace: %d" % self.scope.sample_count)
    
    def do_factor_samples_per_trace(self, args):
        """
        Multiply the number of samples per trace by some N <1.0 so that we
        only capture and store some fraction of the whole trace.
        Arguments:
        - float factor - Percentage of current samples per trace to keep.
        """

        args = shlex.split(args)
        if(len(args) != 1):
            print("set_samples_per_trace expects 1 argument")
            return

        if(self.__check_scope() == False):

            print("No active oscilliscipe connection.")

        else:

            print("Previous samples per trace: %d" % self.scope.sample_count)
            self.scope.sample_count *= float(args[0])
            self.scope.sample_count = int(self.scope.sample_count)
            print("New samples per trace: %d" % self.scope.sample_count)

        

    def do_find_sample_rate(self,args):
        """
        Tries to find the best sample rate and count for capturing traces
        given a particular operating frequency for the target.

        Arguments:
        - int cpu_freq - Target device frequency in Hz
        - float trig_threshold - Threshold of the trigger signal
        - str trig_channel - Scope channel acting as the trigger.
        """
        args = shlex.split(args)
        if(len(args) != 3):
            print("find_sample_rate expects 3 arguments")
            return

        cpu_freq, trig_threshold, trig_channel = args
        cpu_freq        = int(float(cpu_freq))
        trig_threshold  = float(trig_threshold)

        print("Searching for best sample rate with:")
        print("- Target frequency:  %dHz" % cpu_freq)
        print("- Trigger threshold: %fV" % trig_threshold)
        print("- Scope Channel:     %s" % trig_channel)
        print("Working...")
        
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        elif(self.__check_scope() == False):

            print("No active oscilliscipe connection.")

        else:

            scount = self.scope.FindBestSampleRate(self.comms, cpu_freq,
                trig_threshold,trig_channel)
            
            print("Sample rate found: %fHz" % self.scope.sample_frequency)
            print("Samples per trace: %d" % self.scope.sample_count)


    def capture_traces(num_traces, scope, comms, key):
        """
        Capture the supplied number of traces and put them in storage.
        """
        storage         = SAFTraceWriter()
        
        pb = tqdm(range(0,num_traces))
        pb.set_description("Capturing Trace Set")
        
        edec = SassEncryption()
        comms.doSetKey(key)

        for i in pb:
            
            try:
                message         = edec.GenerateMessage()

                comms.doSetMsg(message)

                scope.StartCapture()
                comms.doEncrypt()
                scope.WaitForReady()
                
                data  = scope.GetData(scope.sample_channel)
                storage.AddTrace(message,data)

                if(i%20 == 0) :
                    # Every 20'th trace, check we get the right values.
                    SAFShell.check_encryption_correctness(comms,edec)
                    # Put the key back to how it should be.
                    comms.doSetKey(key)

            except SassCommsException as ex:
                recovered = False
                for i in range(0, 100):
                    if(comms.doHelloWorld()):
                        recovered = True
                        break
                if(not recovered):
                    raise Exception("Could not recover from comms error")

        return storage


    def check_encryption_correctness(comms, edec):
        """
        Make sure we get the right answer when encrypting and decrypting.
        """
        key                 = edec.GenerateKeyBits()
        plaintext           = edec.GenerateMessage()
        aes                 = pyaes.AESModeOfOperationECB(key)
        oracle_ciphertext   = aes.encrypt(plaintext)

        comms.doSetKey(key)
        comms.doSetMsg(plaintext)
        comms.doEncrypt()
        test_ciphertext     = comms.doGetCipher()

        if(oracle_ciphertext != test_ciphertext):
            print("Encypt error: Oracle = %s, Test = %s" % (
                oracle_ciphertext.hex(), test_ciphertext.hex()))
            return False
        else:
            return True

    def do_capture_traces(self, args):
        """
        Capture a sets of traces

        Expects three arguments:
        - num_traces        - How many to cpautre
        - set_tracefile     - Where to store them
        """
        args = shlex.split(args)
        if(len(args) != 2):
            print("capture_traces expects 2 arguments")
            return
        
        numtraces, set_file = args
        numtraces = int(numtraces)
        set_file  = normal_filepath(set_file)
        
        if(self.__check_comms() == False):
        
            print("No currently active connection.")

        elif(self.__check_scope() == False):

            print("No active oscilliscipe connection.")

        else:
            
            print("Capturing trace set...")
            edec = SassEncryption()
            key  = edec.GenerateKeyBits(16)

            print("Key: %s" % key.hex())
            print("Samples per trace: %d" % self.scope.sample_count)

            traces = SAFShell.capture_traces(
                numtraces, self.scope, self.comms,key
            )

            print("Writing tracefile: %s" % set_file)
            traces.trace_description = "key: %s" % key.hex()
            traces.trace_description += "\nSample freq: %fHz" % (
                self.scope.sample_frequency)
            traces.DumpTRS(set_file)

    def do_trace_info(self,args):
        """
        Print information about a trace file.

        Arguments:
        - filepath
        """
        args = shlex.split(args)
        if(len(args) != 1):
            print("capture_ttest expects 3 arguments")
            return

        tpath = args[0]
        tpath = normal_filepath(tpath)

        tfile = SAFTraceSet.LoadTRS(tpath, infoOnly=True)

        print("%s" % tpath)
        print("Number of traces     : %d" % tfile.num_traces)
        print("Length of trace      : %d" % tfile.trace_length)
        print("Length of plaintext  : %d" % tfile.plaintext_length)
        print("Data Encoding        : %d" % int.from_bytes(tfile.coding_type,"little"))
        print("Trace Description    : ")
        print("\t", tfile.trace_description.replace("\n","\n\t"))

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
            
            cap = SAFTTestCapture(self.comms,self.scope,num_traces=numtraces,
                trace_channel = self.trace_channel)

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


    def do_cpa_attack(self, args):
        """
        Run a CPU attack on a trace set.

        Setting from=0, to=-1 will examine the whole trace.

        arguments:
        -   traceset:   The trace set to load and attack
        -   from:       Start from this sample
        -   to:         Stop at this sample
        -   graph:      Where to save the CPA analysis figures too.
        """

        args = shlex.split(args)

        if(not len(args) == 4):
            
            print("Command expects two arguments. Got %d."%len(args))

        else:
            
            attack = SAFAttackCPA(normal_filepath(args[0]))
            attack.isolate_start = int(args[1])
            attack.isolate_end   = int(args[2])
            
            fig = attack.run()


    def do_trace_energy_aggregate(self, args):
        """
        Transforms all of the traces such that each sample represents the
        total *energy* consumed in a *single clock cycle*. As opposed to the
        standard representation where each sample is the instantaneous energy
        per clock cycle.
        
        :todo: Finish implementing this.

        Arguments:
            - t_in  - Input trace set path
            - t_out - Output trace set path
            - samples_per_cycle - Number of samples per clock cycle.
        """
        args = shlex.split(args)

        if(not len(args) == 3):
            
            print("Command expects three arguments. Got %d."%len(args))

        else:

            t_in, t_out, samples_per_cycle = args
            samples_per_cycle = int(samples_per_cycle)
            
            traces = SAFTraceSet.LoadTRS(t_in)

            original_trace_len = traces.trace_length
            
            print("Aggregating over %d samples")
            traces.AggregatePerCycle(samples_per_cycle)

            print("New trace length: %d" % traces.trace_length)

            print("Writing traces to %s" % t_out)
            traces.DumpTRS(t_out)
            del traces


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

