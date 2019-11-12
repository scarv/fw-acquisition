
FW_ACQUISITION_BUILD = build/

#
# Build the doxygen documentation for the target code skeleton.
#
docs-target:
	@mkdir -p $(FW_ACQUISITION_BUILD)
	doxygen target/doxygen.conf

