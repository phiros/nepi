SRCDIR      = $(CURDIR)/src
TESTDIR     = $(CURDIR)/test
TESTLIB  = $(TESTDIR)/lib
BUILDDIR    = $(CURDIR)/build
DISTDIR     = $(CURDIR)/dist

SUBBUILDDIR = $(shell python -c 'import distutils.util, sys; \
	      print "lib.%s-%s" % (distutils.util.get_platform(), \
	      sys.version[0:3])')
PYTHON25 := $(shell python -c 'import sys; v = sys.version_info; \
    print (1 if v[0] <= 2 and v[1] <= 5 else 0)')

ifeq ($(PYTHON25),0)
BUILDDIR := $(BUILDDIR)/$(SUBBUILDDIR)
else
BUILDDIR := $(BUILDDIR)/lib
endif

PYPATH = $(BUILDDIR):$(TESTLIB):$(PYTHONPATH)
COVERAGE = $(or $(shell which coverage), $(shell which python-coverage), \
	   coverage)

all: clean
	PYTHONPATH="$(PYTHONPATH):$(SRCDIR)" ./setup.py build

install: all
	PYTHONPATH="$(PYTHONPATH):$(SRCDIR)" ./setup.py install

test: all
	retval=0; \
	       for i in `find "$(TESTDIR)" -iname '*.py' -perm -u+x -type f`; do \
	       echo $$i; \
	       PYTHONPATH="$(PYPATH)" $$i -v || retval=$$?; \
	       done; exit $$retval

test-one: all
	echo $(file) $(case)
	PYTHONPATH="$(PYPATH)" $(file) $(case)

coverage: all
	rm -f .coverage
	for i in `find "$(TESTDIR)" -perm -u+x -type f`; do \
		set -e; \
		PYTHONPATH="$(PYPATH)" $(COVERAGE) -x $$i -v; \
		done
	$(COVERAGE) -c
	$(COVERAGE) -r -m `find "$(BUILDDIR)" -name \\*.py -type f`
	rm -f .coverage

clean:
	rm -f `find -name \*.pyc` .coverage *.pcap
	rm -rf "$(BUILDDIR)"

distclean: clean
	rm -rf "$(DISTDIR)"

MANIFEST:
	find . -path ./.hg\* -prune -o -path ./build -prune -o \
		-name \*.pyc -prune -o -name \*.swp -prune -o \
		-name MANIFEST -prune -o -type f -print | \
		sed 's#^\./##' | sort > MANIFEST

dist: MANIFEST
	./setup.py sdist

.PHONY: all clean distclean dist test coverage install MANIFEST
