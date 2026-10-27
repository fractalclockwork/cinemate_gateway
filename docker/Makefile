# Run from repo root: make -C docker <target>
# Adapted from crt-drive docker/Makefile (Dev-Host pico-dev; no Pi gateway).

DOCKER_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
REPO_ROOT := $(abspath $(DOCKER_DIR)/..)

include $(DOCKER_DIR)TOOLCHAIN_VERSIONS
export BASE_IMAGE_DEBIAN PICO_SDK_VERSION PICOTOOL_VERSION

DEV_UID ?= $(shell id -u)
DEV_GID ?= $(shell id -g)
export DEV_UID DEV_GID

WITH_DOCKER := $(DOCKER_DIR)with-docker.sh

COMPOSE := $(WITH_DOCKER) docker compose --env-file $(DOCKER_DIR)TOOLCHAIN_VERSIONS -f $(DOCKER_DIR)docker-compose.yml
COMPOSE_USB := $(COMPOSE) -f $(DOCKER_DIR)docker-compose.usb.yml
COMPOSE_PLATFORM = $(WITH_DOCKER) docker compose --env-file $(DOCKER_DIR)TOOLCHAIN_VERSIONS \
	-f $(DOCKER_DIR)docker-compose.yml \
	-f $(DOCKER_DIR)docker-compose.platform-$(PLATFORM_TAG).yml

ifeq ($(wildcard $(REPO_ROOT)/.venv/bin/python),)
LOAD_PYTHON := python3
else
LOAD_PYTHON := $(REPO_ROOT)/.venv/bin/python
endif

UNAME_M := $(shell uname -m)
ifeq ($(UNAME_M),x86_64)
  HOST_PLATFORM := linux/amd64
else ifeq ($(UNAME_M),aarch64)
  HOST_PLATFORM := linux/arm64
else ifeq ($(UNAME_M),arm64)
  HOST_PLATFORM := linux/arm64
else
  HOST_PLATFORM := linux/$(UNAME_M)
endif

ifeq ($(HOST_PLATFORM),linux/amd64)
  PLATFORM_TAG := amd64
else ifeq ($(HOST_PLATFORM),linux/arm64)
  PLATFORM_TAG := arm64
else
  PLATFORM_TAG :=
endif

# Cached CircuitPython UF2 (operator downloads; not committed).
CIRCUITPYTHON_UF2 ?= /workspace/archive/cache/circuitpython/raspberry_pi_pico.uf2

.PHONY: help print-host-platform build-images build-images-host smoke \
	shell shell-usb check pico-discover picotool-info load-circuitpython

help:
	@echo "ir-remote-bose pico-dev (Dev-Host, adapted from crt-drive)"
	@echo "  make build-images / smoke / shell / shell-usb"
	@echo "  make check              — pytest SIL inside the container"
	@echo "  make pico-discover      — host lsusb + optional picotool (BOOTSEL)"
	@echo "  make picotool-info      — picotool info via USB compose"
	@echo "  make load-circuitpython — picotool load UF2 (needs HUMAN_VERIFY + HUMAN_FLASH + present pass)"
	@echo "  CIRCUITPYTHON_UF2=$(CIRCUITPYTHON_UF2)"
	@echo "See README.md and ../environment/README.md"

print-host-platform:
	@echo $(HOST_PLATFORM)

build-images: build-images-host

build-images-host:
ifeq ($(PLATFORM_TAG),)
	@echo "=== docker compose build (host: $(HOST_PLATFORM); no amd64/arm64 override) ==="
	$(COMPOSE) build
else
	@echo "=== docker compose build (host: $(HOST_PLATFORM)) ==="
	$(COMPOSE_PLATFORM) build
endif

smoke: build-images
	$(COMPOSE) run --rm --no-deps pico-dev bash -lc 'set -euo pipefail; \
		arm-none-eabi-gcc --version; cmake --version; ninja --version; \
		test -n "$$PICO_SDK_PATH"; test -f "$$PICO_SDK_PATH/pico_sdk_init.cmake"; \
		echo "PICO_SDK_PATH=$$PICO_SDK_PATH"; \
		picotool_out=$$(picotool version 2>&1); printf "%s\n" "$$picotool_out"; \
		if printf "%s\n" "$$picotool_out" | grep -qi "without USB support"; then \
			echo "picotool was built without libusb/USB support" >&2; exit 1; fi; \
		python3 --version'

shell:
	$(COMPOSE) run --rm --no-deps -it pico-dev bash

shell-usb:
	$(COMPOSE_USB) run --rm --no-deps -it pico-dev bash

check: build-images
	$(COMPOSE) run --rm --no-deps pico-dev bash -lc 'set -euo pipefail; \
		python3 -m venv /tmp/ir-gateway-venv; \
		/tmp/ir-gateway-venv/bin/pip install -q -r /workspace/requirements.txt; \
		cd /workspace && PYTHONPATH=/workspace /tmp/ir-gateway-venv/bin/pytest -q'

pico-discover:
	@bash $(REPO_ROOT)/environment/pico_discover.sh
	@echo "=== picotool (container, USB) ==="
	@if lsusb -d 2e8a:0003 >/dev/null 2>&1; then \
		$(COMPOSE_USB) run --rm --no-deps pico-dev bash -lc 'picotool info -a'; \
	else \
		echo "skipping picotool info (board is not in BOOTSEL 2e8a:0003)."; \
	fi

picotool-info:
	$(COMPOSE_USB) run --rm --no-deps pico-dev bash -lc 'picotool info -a || picotool info'

load-circuitpython:
	@test "$${HUMAN_VERIFY:-}" = "1" || { echo "set HUMAN_VERIFY=1 (operator verifies the bench before this test begins)" >&2; exit 1; }
	@test "$${HUMAN_FLASH:-}" = "1" || { echo "set HUMAN_FLASH=1 (operator allows the firmware write)" >&2; exit 1; }
	@PYTHONPATH=$(REPO_ROOT) $(LOAD_PYTHON) -c "from harness.boards import stage_passed; import sys; sys.exit(0 if stage_passed('pico', 'present') else 1)" \
		|| { echo "pico present stage has not passed. Next: HUMAN_VERIFY=1 make stage BOARD=pico STAGE=present" >&2; exit 1; }
	@test -f "$(REPO_ROOT)/archive/cache/circuitpython/raspberry_pi_pico.uf2" || { \
		echo "missing archive/cache/circuitpython/raspberry_pi_pico.uf2 — download CircuitPython UF2 for raspberry_pi_pico first" >&2; \
		exit 1; }
	$(COMPOSE_USB) run --rm --no-deps pico-dev bash -lc 'set -euo pipefail; \
		test -f $(CIRCUITPYTHON_UF2) || { echo "missing $(CIRCUITPYTHON_UF2)" >&2; exit 1; }; \
		echo "Loading CircuitPython UF2 via environment/flash.sh (reboot -u -f, then load -x)..."; \
		bash /workspace/environment/flash.sh $(CIRCUITPYTHON_UF2); \
		echo "After reboot, mount CIRCUITPY and run: HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware"'
