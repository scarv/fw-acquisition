# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = fw-acquisition
SOURCEDIR     = $(abspath ../../work/sphinx-apidoc)
BUILDDIR      = $(abspath ../../work/api-docs)
LIB_PATH      = $(abspath ../../sassrig)

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile apidocs

apidocs:
	sphinx-apidoc -P -f -o "$(SOURCEDIR)" -e -a "$(LIB_PATH)"
	cp ./index.rst $(SOURCEDIR)/index.rst
	sed -i "s/:members:/:members:\n    :inherited-members:/" \
        $(SOURCEDIR)/*.rst
	sed -i "s/:members:/:members:\n    :private-members:/" \
        $(SOURCEDIR)/*.rst

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile apidocs
	@$(SPHINXBUILD) -c ./ "$(SOURCEDIR)" "$(BUILDDIR)" \
        $(SPHINXOPTS) $(O)
	echo "Documentation Written to $(BUILDDIR)/index.html"
