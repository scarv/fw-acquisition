
# SASS-RIG

This is the SCARV Side channel AnalySis Suite Rig.

It is used to automate the generation, running, analysis and archiving of
encryption/decription artifacts.

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

