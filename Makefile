BOARD ?= pico
STAGE ?= present
export BOARD
PYTHON ?= python3
ifneq ($(wildcard .venv/bin/python),)
PYTHON := .venv/bin/python
endif

export PYTHONPATH := $(CURDIR):$(PYTHONPATH)

.PHONY: venv check check-docker sim stage loopback capture firmware \
	firmware-keymap image smoke shell shell-usb pico-discover \
	picotool-info load-circuitpython help

help:
	@echo "ir-remote-bose — host checks and Pico IR→HID"
	@echo "  Host:           make check | sim | firmware-keymap"
	@echo "  Bench:          make stage | loopback | capture | firmware"
	@echo "  Docker:         make image | smoke | check-docker | shell | shell-usb"
	@echo "  USB:            make pico-discover | picotool-info | load-circuitpython"
	@echo "Operator flags: OPERATOR_VERIFY / OPERATOR_FLASH / OPERATOR_IR_PATH"

venv:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt

check:
	$(PYTHON) -m pytest -q

check-docker:
	$(MAKE) -C docker check

sim:
	$(PYTHON) -c "from hardware.records import load_board; from software.fixture import run_fixture; \
print(run_fixture(load_board('$(BOARD)')))"

stage:
	$(PYTHON) -m hardware.stages --board $(BOARD) --stage $(STAGE)

loopback:
	$(PYTHON) -m hardware.loopback --board $(BOARD)

BUTTON ?=
PROFILE ?=
FRESH ?=
MODE ?= unique
READY_WAIT ?= 0
capture:
ifeq ($(MODE),unique)
	$(PYTHON) -m hardware.capture --board $(BOARD) --unique $(if $(FRESH),--fresh,) $(if $(READY_WAIT),--ready-wait $(READY_WAIT),)
else ifeq ($(MODE),confirm)
	$(PYTHON) -m hardware.capture --board $(BOARD) --confirm-map $(if $(READY_WAIT),--ready-wait $(READY_WAIT),)
else
	$(PYTHON) -m hardware.capture --board $(BOARD) --validate $(if $(BUTTON),--button $(BUTTON),) $(if $(PROFILE),--profile $(PROFILE),) $(if $(FRESH),--fresh,) $(if $(READY_WAIT),--ready-wait $(READY_WAIT),)
endif

firmware-keymap:
	$(PYTHON) -m software.export_firmware_keymap

firmware: firmware-keymap
	$(PYTHON) -m hardware.firmware --board $(BOARD)

image:
	$(MAKE) -C docker build-images

smoke:
	$(MAKE) -C docker smoke

shell:
	$(MAKE) -C docker shell

shell-usb:
	$(MAKE) -C docker shell-usb

pico-discover:
	$(MAKE) -C docker pico-discover

picotool-info:
	$(MAKE) -C docker picotool-info

load-circuitpython:
	$(MAKE) -C docker load-circuitpython
