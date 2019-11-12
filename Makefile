
FW_ACQUISITION_BUILD = build/

#
# Build the doxygen documentation for the target code skeleton.
#
docs-target:
	@mkdir -p $(FW_ACQUISITION_BUILD)
	doxygen target/doxygen.conf

#
# Build the Sphinx documentation for the host scass library.
#
docs-scass:
	@mkdir -p $(FW_ACQUISITION_BUILD)
	rm docs/source/scass.*.rst
	sphinx-apidoc -o docs/source ./scass
	make -C docs html
	rm -fr                 build/sphinx-docs
	mv -f  docs/build/html build/sphinx-docs


#
# Check we can build the scass_target object file without warnings.
#
target-obj:
	$(CC) -m32 -Wall -c -o build/scass_target.o target/scass/scass_target.c

