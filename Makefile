SHELL=/bin/bash
PYTHON=`which python`
NAME=`python setup.py --name`
VERSION=`python setup.py --version`
SDIST=dist/$(NAME)-$(VERSION).tar.gz

# Fixes clang compile errors
ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future

all: check test source deb

dist: source deb

source:
	$(PYTHON) setup.py sdist

deb:
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

rpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

install:
	$(PYTHON) setup.py install --install-layout=deb

develop:
	source venv/bin/activate && python setup.py develop

test: venv develop
	source venv/bin/activate && python setup.py test

check: venv

venv:
	test -d venv || virtualenv venv
	source venv/bin/activate && python setup.py install

init: clean venv

daily:
	$(PYTHON) setup.py bdist egg_info --tag-date

deploy:
	# make sdist
	rm -rf dist
	python setup.py sdist

	# setup venv
	rm -rf $(VENV)
	virtualenv --no-site-packages $(VENV)
	$(VENV)/bin/pip install $(SDIST)

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST dist build iputil.egg-info deb_dist venv cache
	find . -name '*.pyc' -delete
