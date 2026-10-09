# ============================================================================
# oowlet-recommend-uc — recommendation engine for content and people
#
#   make build      venv → protos → byte-compile → import check →
#                     dist/oowlet_recommend_uc-<ver>-py3-none-any.whl   (pip-installable)
#                     dist/oowlet-recommend-uc                          (single executable)
#   make env        venv/ with requirements-dev.txt (automatic for every target;
#                   use another venv with VENV=<dir>)
#   make proto      generate oowlet/gen/** from $(PROTO_DIR) (recommenduc, eventlayer, feature_service)
#   make check      protos + byte-compile + import every module (no packaging)
#   make wheel      dist/*.whl only
#   make exe        dist/oowlet-recommend-uc only (PyInstaller, one file)
#   make image      Docker image (built from the repository root, needs ../proto)
#   make test       unit + end-to-end tests (gRPC, fake event layer, fake feature service)
#   make run-check  validate the configuration, reach the event layer and the feature service
#   make run        start the server from source (configuration: RUC_* env vars)
#
# The executable runs on Linux machines of the same CPU architecture with a
# glibc at least as new as the build machine's; Python need not be installed.
#   dist/oowlet-recommend-uc            start the gRPC API and the event consumer
#   dist/oowlet-recommend-uc check      configuration + dependencies reachable
#   dist/oowlet-recommend-uc version    version, commit, build time
# ============================================================================

NAME       := oowlet-recommend-uc
PROTO_DIR  ?= ../proto
BUILD_DIR  ?= build
DIST_DIR   ?= dist
VERSION    ?= $(shell sed -n 's/^ *version="\([^"]*\)".*/\1/p' setup.py)
COMMIT     ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)
VENV       ?= venv
PYTHON     := $(VENV)/bin/python
PIP        := $(PYTHON) -m pip
# Written after a successful install. Its name carries a hash of the
# requirements files, so any change to their content (not their timestamps —
# an unpacked archive keeps old ones) re-runs the install.
REQ_HASH   := $(shell cat requirements.txt requirements-dev.txt 2>/dev/null | sha256sum | cut -c1-16)
VENV_STAMP := $(VENV)/.deps-$(REQ_HASH)
PACKAGES   := ruc oowlet
EXE        := $(DIST_DIR)/$(NAME)
# Where `make build` / `make install` put the executable. Default: this
# module's bin/ (like the security service). Elsewhere: BIN_DIR=/usr/local/bin
BIN_DIR    ?= bin
INSTALLED  := $(BIN_DIR)/$(NAME)
IMAGE      ?= $(NAME):$(VERSION)

.PHONY: help env _check-venv proto check build-info wheel exe install uninstall build image test lint run run-check clean

help:
	@echo "oowlet-recommend-uc"
	@echo "  make build       venv, protos, checks, wheel + executable in $(DIST_DIR)/"
	@echo "  make check       protos, byte-compile, import check (no packaging)"
	@echo "  make wheel       $(DIST_DIR)/*.whl"
	@echo "  make exe         $(EXE) (single file, no Python needed to run it)"
	@echo "  make install     copy the executable to BIN_DIR=$(BIN_DIR) (make build does this too)"
	@echo "  make uninstall   remove $(INSTALLED)"
	@echo "  make image       Docker image $(IMAGE)"
	@echo "  make env         create $(VENV)/ (requirements-dev.txt)"
	@echo "  make proto       generate oowlet/gen from PROTO_DIR=$(PROTO_DIR)"
	@echo "  make test        tests (no services needed)"
	@echo "  make run-check   configuration + event layer + feature service reachable"
	@echo "  make run         start the server from source"
	@echo "  make clean       remove generated code, build output and caches"

env: $(VENV_STAMP)

$(VENV_STAMP):
	@command -v python3 >/dev/null || { echo "✗ python3 not found"; exit 1; }
	@if ! $(PYTHON) -m pip --version >/dev/null 2>&1; then \
		echo "Creating $(VENV)/ ..."; \
		rm -rf $(VENV); \
		python3 -m venv $(VENV) || { rm -rf $(VENV); \
			echo "✗ could not create $(VENV)/ (Debian/Ubuntu: sudo apt-get install python3-venv)"; exit 1; }; \
	fi
	@$(PIP) install --quiet --upgrade pip
	@$(PIP) install --quiet -r requirements-dev.txt || { echo "✗ pip install -r requirements-dev.txt failed"; exit 1; }
	@$(MAKE) --no-print-directory _check-venv
	@rm -f $(VENV)/.deps-* && touch $@
	@echo "✓ $(VENV) ready ($$($(PYTHON) --version))"

_check-venv:
	@$(PYTHON) -c 'import grpc, google.protobuf, numpy, grpc_tools, pytest, PyInstaller, setuptools, wheel' || \
		{ echo "✗ $(VENV)/ is missing packages — run: rm -f $(VENV)/.deps-* && make env"; exit 1; }

proto: $(VENV_STAMP)
	@for d in recommenduc eventlayer feature_service; do \
		test -d "$(PROTO_DIR)/$$d" || { echo "✗ $(PROTO_DIR)/$$d not found (set PROTO_DIR)"; exit 1; }; \
	done
	@$(PYTHON) scripts/gen_protos.py $(PROTO_DIR)

check: proto
	@$(PYTHON) -m compileall -q $(PACKAGES)
	@$(PYTHON) scripts/import_check.py

# Version, commit and build time, compiled into the wheel and the executable
# (`oowlet-recommend-uc version`).
build-info:
	@mkdir -p $(BUILD_DIR)
	@printf 'VERSION = "%s"\nCOMMIT = "%s"\nBUILT = "%s"\n' "$(VERSION)" "$(COMMIT)" "$$(date -u +%Y-%m-%dT%H:%M:%SZ)" > ruc/_build_info.py
	@printf 'service=$(NAME)\nversion=%s\ncommit=%s\n' "$(VERSION)" "$(COMMIT)" > $(BUILD_DIR)/BUILD_INFO

wheel: check build-info
	@mkdir -p $(DIST_DIR)
	@rm -f $(DIST_DIR)/oowlet_recommend_uc-*.whl
	@$(PIP) wheel --quiet --no-deps --no-build-isolation -w $(DIST_DIR) . || { echo "✗ wheel build failed"; exit 1; }
	@rm -rf *.egg-info build/lib build/bdist.*
	@rmdir build 2>/dev/null || true
	@echo "✓ wheel: $$(ls $(DIST_DIR)/oowlet_recommend_uc-*.whl)"

# One self-contained file: the Python runtime, every dependency and all of the
# engine's modules. --collect-submodules makes sure modules that are only
# imported lazily are packed too; the selftest imports every one of them from
# inside the executable.
exe: check build-info
	@mkdir -p $(DIST_DIR) $(BUILD_DIR)/pyinstaller
	@rm -f $(EXE)
	@$(PYTHON) -c 'import PyInstaller' 2>/dev/null || \
		{ echo "✗ PyInstaller is not installed in $(VENV)/ — run: rm -f $(VENV)/.deps-* && make build"; exit 1; }
	@$(PYTHON) -m PyInstaller --noconfirm --clean --log-level WARN --onefile \
		--name $(NAME) \
		--distpath $(abspath $(DIST_DIR)) \
		--workpath $(abspath $(BUILD_DIR))/pyinstaller \
		--specpath $(abspath $(BUILD_DIR))/pyinstaller \
		--paths $(CURDIR) \
		$(foreach p,$(PACKAGES),--collect-submodules $(p)) \
		--collect-submodules numpy._core \
		--exclude-module pytest --exclude-module grpc_tools \
		--exclude-module setuptools --exclude-module pkg_resources \
		$(CURDIR)/scripts/entry.py || { echo "✗ executable build failed"; exit 1; }
	@cd /tmp && $(abspath $(EXE)) selftest || { echo "✗ $(EXE) is incomplete"; exit 1; }
	@$(EXE) version
	@echo "✓ executable: $(EXE) ($$(du -h $(EXE) | cut -f1))"

# Copies the built executable to BIN_DIR (mode 0755). Written to a temporary
# name first and renamed, so a running copy is never overwritten in place.
# Builds the executable first only if it is missing.
install:
	@[ -x "$(EXE)" ] || $(MAKE) --no-print-directory exe
	@mkdir -p $(BIN_DIR) 2>/dev/null || { echo "✗ cannot create $(BIN_DIR)/ (permissions? e.g. sudo make install BIN_DIR=$(BIN_DIR))"; exit 1; }
	@install -m 0755 $(EXE) $(INSTALLED).tmp.$$$$ && mv -f $(INSTALLED).tmp.$$$$ $(INSTALLED) || \
		{ rm -f $(INSTALLED).tmp.*; echo "✗ cannot write $(BIN_DIR)/ (permissions? e.g. sudo make install BIN_DIR=$(BIN_DIR))"; exit 1; }
	@$(INSTALLED) version >/dev/null || { echo "✗ $(INSTALLED) does not run"; exit 1; }
	@echo "✓ installed $(INSTALLED)"

uninstall:
	@rm -f $(INSTALLED)
	@echo "✓ removed $(INSTALLED)"

build: wheel exe
	@$(MAKE) --no-print-directory install
	@echo ""
	@echo "✓ built $(NAME) $(VERSION) ($(COMMIT))"
	@echo "    $(INSTALLED)      (installed)"
	@echo "    $(EXE)"
	@echo "    $$(ls $(DIST_DIR)/oowlet_recommend_uc-*.whl)"
	@echo "  run: $(INSTALLED)            (configuration: RUC_* environment variables, see .env.example)"
	@echo "       $(INSTALLED) check      (configuration + dependencies reachable)"

# Built from the repository root because the image needs ../proto.
image:
	@command -v docker >/dev/null || { echo "✗ docker not found"; exit 1; }
	@docker build -f $(CURDIR)/Dockerfile \
		--build-arg VERSION=$(VERSION) --build-arg COMMIT=$(COMMIT) \
		-t $(IMAGE) $(abspath $(PROTO_DIR)/..)
	@echo "✓ image $(IMAGE)"

test: $(VENV_STAMP)
	@$(PYTHON) -m pytest -q

lint: $(VENV_STAMP)
	@$(PYTHON) -m pyflakes ruc tests 2>/dev/null || \
		echo "(pyflakes not installed: pip install pyflakes)"

run-check: $(VENV_STAMP)
	@$(PYTHON) -m ruc.cli check

run: $(VENV_STAMP)
	@$(PYTHON) -m ruc.cli serve

clean:
	@rm -rf oowlet/gen oowlet/.gen-stage $(BUILD_DIR) $(DIST_DIR) *.egg-info .pytest_cache ruc/_build_info.py
	@find . -name __pycache__ -type d -prune -not -path "./$(VENV)/*" -exec rm -rf {} +
	@echo "✓ cleaned"
