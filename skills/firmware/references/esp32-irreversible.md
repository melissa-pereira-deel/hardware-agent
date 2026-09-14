# ESP32 irreversible operations - advisory only

Everything in this file is **T3**. Draft the command, explain it, stop. Do not execute.

## Why eFuses are different

eFuse bits are one-time programmable: **they can only change from 0 to 1, never back**. esptool's own tooling makes you type `BURN` in all capitals to continue, because the operation is irreversible.

Consequences of getting one wrong:

- **Wrong secure boot key burned** -> the chip will only boot images signed with a key you no longer have. Permanently unbootable.
- **Flash encryption enabled in release mode** -> you can no longer read or reflash the chip over serial. If the OTA path has a bug, the device is dead in the field.
- **`SPI_BOOT_CRYPT_CNT` exhausted** -> no further re-encryption possible.
- **Disabled JTAG / disabled download mode** -> no debugging, no recovery.

## The commands (draft these, never run them)

```bash
espefuse --port <PORT> burn_key <block> <keyfile> <purpose>
espefuse --port <PORT> burn_efuse <EFUSE_NAME> <value>
espefuse --port <PORT> burn_bit <block> <bit>
```

esptool v5 deprecated the `.py` suffix; `espefuse.py` still works but warns.

### Secure Boot v2 is not a command

There is **no `idf.py secure-boot-enable`.** An earlier version of this file
said there was, which is worse than saying nothing — it looks authoritative and
it does not exist. The actual flow:

1. `idf.py menuconfig` → Security features → *Enable hardware Secure Boot in
   bootloader*
2. `idf.py bootloader` — builds the secure bootloader
3. Flash the bootloader with the `esptool write-flash` command the build prints
4. `idf.py flash` — partition table and app

**The eFuse is not burned by any of those steps.** `ABS_DONE_1` is set **by the
bootloader itself, on first boot**, once a valid partition table and app are
present. That is the detail that matters for safety: the point of no return is
a *power-on*, not a command you can decide not to run. Once that board boots,
it is done.

**So the flash is the gate, not the eFuse command.**

This is the operationally important consequence and it inverts the usual tier
logic. Flashing a bootloader is normally T2 — reversible, you re-flash. But
flashing a bootloader *built with secure boot or flash encryption enabled* is
**T3**, because the next power-on burns the eFuse and there is no command left
to decline. The command line looks identical either way:

```bash
esptool --port <PORT> write-flash 0x0 bootloader.bin    # T2 or T3 - the
idf.py -p <PORT> flash                                   # command cannot tell you
```

Nothing in that text distinguishes the two cases; the difference lives in
`sdkconfig`. So neither the risk broker nor a reader of the command can
classify it. **You have to know what you built.** Before flashing any
bootloader to a unit you care about, check:

```bash
grep -E "SECURE_BOOT|FLASH_ENC" sdkconfig
```

If either is enabled, treat the flash as T3: hand it over, do not execute it.
`run_device_write` enforces the disclosure half of this — it refuses a
bootloader flash whose `what_changes` does not state secure-boot and
flash-encryption status.

The real `idf.py` security subcommands are `secure-generate-signing-key`,
`secure-sign-data` and `secure-verify-signature`. None of them burn anything.

*Verified against Espressif ESP-IDF Secure Boot v2 documentation, 2026-09-14:*
https://docs.espressif.com/projects/esp-idf/en/stable/esp32/security/secure-boot-v2.html

## The response shape when this comes up

1. State plainly that this is irreversible and can permanently brick the chip.
2. Give the exact command with the exact device port.
3. Explain what each argument does and what state the chip will be in afterwards.
4. Name the recovery path - and if there isn't one, say so.
5. Recommend testing the entire flow on a **sacrificial dev board** first.
6. Stop. The person runs it.

## Related irreversible-ish operations

- **AVR fuse writes** (`avrdude -U lfuse:w:...`): setting the wrong clock source or disabling reset/SPI can make the chip unreachable without a high-voltage programmer.
- **Bootloader replacement** on boards without a recovery mode.

## Production sequencing

Security features should be enabled **last**, after OTA has been proven to work end to end on unsecured units. Enabling secure boot before the update path is trusted is the standard way to strand a batch.
