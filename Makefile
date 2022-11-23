SOURCE = bigorm
BINDIR = .venv/bin/
PYTHON3 = $(BINDIR)python3
SYSPYTHON = python3.10

test:
	$(BINDIR)pytest tests

lint:
	$(BINDIR)black $(SOURCE)
	$(BINDIR)flake8 $(SOURCE)
	$(BINDIR)trailing-whitespace-fixer
	$(BINDIR)end-of-file-fixer

install:
	$(SYSPYTHON) -m venv .venv
	$(BINDIR)pip install -r requirements.dev.txt
	$(PYTHON3) setup.py install
	$(PYTHON3) setup.py develop
