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
espefuse.py --port <PORT> burn_key <block> <keyfile> <purpose>
espefuse.py --port <PORT> burn_efuse <EFUSE_NAME> <value>
espefuse.py --port <PORT> burn_bit <block> <bit>
idf.py secure-boot-enable          # and related secure boot flows
```

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
