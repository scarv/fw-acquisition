
# SASS-RIG

This is the SCARV Side channel AnalySis Suite Rig.

It is used to automate the generation, running, analysis and archiving of
encryption/decription artifacts.

## Getting Started

In order to connect to the picoscope, follow the instructions
[here](https://www.picotech.com/downloads) to install the drivers for your
system and scope model. This flow was developed using the
PicoScope 5000 series.

These commands will get you setup and running with the flow. Setting up the
physical test rig is not documented here, but a link will be forthcoming.

```sh
$> git clone https://github.com/scarv/sass-rig.git
$> cd sass-rig
$> sudo pip3 install -r requirements.txt
$> ./sass.py --help

usage: sass.py [-h] [-v] {capture,test,attack,custom} ...

positional arguments:
  {capture,test,attack,custom}
    capture             Capture traces from a test rig
    test                Test the connection to the target test rig
    attack              Try to recover the key from a set of captured traces
    custom              Run whatever the custom command is on the target

optional arguments:
  -h, --help            show this help message and exit
  -v                    Turn on verbose logging.
```

- Capturing traces from a rig is done via the `capture` command. This takes
a single file path as its argument, which contains all flow configuration
options such as port connection speeds, paths, numbers of traces and so on.
An example is the [flow-config.cfg](flow-config.cfg) file.
- Captured traces are attacked with the `attack` command. This will load a
`*.trs` file and try to work out the key using a correlation attack.
- The `custom` command is used as a simple way to test things on the target.
- The `test` target can be used to check that you can properly connect to
the target device, scope and can run the flow correctly.

## Organisation

The rig is split into two components:

- The host side runs the scripts found in `sassrig/`, which are responsible
  for controlling the target.
- The target uses the C code found in `target/` to interface with the host
  program and act according to what it is told to do.

## Capabilities

- Message, Key and Ciphertext generation
- Testbench Communication
  - Key/Message/Ciphertext upload / download.
  - Configuration setting
- Scope / Probe control
  - Trace configuration
  - Trigger configuration
  - Trace capture and compression
- Flow Coordination

