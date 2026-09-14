"""Bootloader-flash disclosure requirement on run_device_write.

Secure Boot v2 is enabled by building a secure bootloader and flashing it; the
eFuse burns on the next power-on. So the irreversible act is a flash whose
command text is indistinguishable from an ordinary one - the difference lives
in sdkconfig, which the broker cannot see.

The broker therefore cannot classify it, and a T3 rule on all bootloader
flashes would fire on every bring-up. Instead the caller must state the status,
which is what surfaces it. These tests pin that behaviour.
"""

from __future__ import annotations

import pytest

from risk_broker import server

ORDINARY_DISCLOSURE = "secure boot disabled, flash encryption disabled, ordinary app flash"

BOOTLOADER_COMMANDS = [
    "esptool --port /dev/cu.usbmodem1101 write-flash 0x0 bootloader.bin",
    "esptool.py --port /dev/cu.usbmodem1101 write_flash 0x1000 bootloader.bin",
    "idf.py -p /dev/cu.usbmodem1101 flash",
    "idf.py flash",
]

NON_BOOTLOADER_COMMANDS = [
    "esptool --port /dev/cu.usbmodem1101 write-flash 0x10000 app.bin",
    "esphome run lamp.yaml",
    "pio run -t upload",
]


@pytest.mark.parametrize("command", BOOTLOADER_COMMANDS)
def test_bootloader_flash_without_disclosure_is_refused(command: str) -> None:
    out = server.run_device_write(
        command=command,
        device="ESP32-C6 devkit on /dev/cu.usbmodem1101",
        what_changes="writes the firmware",
        recovery="re-flash over serial",
    )
    assert out.get("refused") is True, out
    assert "secure-boot and flash-encryption status" in out["why"]
    assert "sdkconfig" in out["why"]


@pytest.mark.parametrize("command", BOOTLOADER_COMMANDS)
def test_bootloader_flash_with_disclosure_passes_the_gate(command: str) -> None:
    """With the status stated, the call proceeds to normal tier handling.

    It may still fail for other reasons (the binary is not installed here), but
    it must not be refused for missing disclosure.
    """
    out = server.run_device_write(
        command=command,
        device="ESP32-C6 devkit on /dev/cu.usbmodem1101",
        what_changes=ORDINARY_DISCLOSURE,
        recovery="re-flash over serial; bootloader is stock",
    )
    why = out.get("why", "")
    assert "secure-boot and flash-encryption status" not in why, out


@pytest.mark.parametrize("command", NON_BOOTLOADER_COMMANDS)
def test_non_bootloader_flashes_do_not_require_disclosure(command: str) -> None:
    """The requirement must not fire on every ordinary upload, or it gets
    routed around - which is how a guardrail dies."""
    out = server.run_device_write(
        command=command,
        device="ESP32-C6 devkit",
        what_changes="writes the application image",
        recovery="re-flash over serial",
    )
    assert "secure-boot and flash-encryption status" not in out.get("why", ""), out


def test_partial_disclosure_is_not_enough() -> None:
    """Naming secure boot but not flash encryption leaves half the question open."""
    out = server.run_device_write(
        command="idf.py -p /dev/cu.usbmodem1101 flash",
        device="devkit",
        what_changes="secure boot is disabled",
        recovery="re-flash",
    )
    assert out.get("refused") is True, out


def test_disclosure_does_not_let_a_t3_command_through() -> None:
    """Disclosure is an additional gate, never a bypass of the tier rules."""
    out = server.run_device_write(
        command="espefuse burn_key BLOCK_KEY0 key.bin SECURE_BOOT_DIGEST0",
        device="devkit",
        what_changes="secure boot enabled, flash encryption disabled",
        recovery="none",
    )
    assert out.get("refused") is True
    assert out.get("use_instead") == "plan_irreversible"
