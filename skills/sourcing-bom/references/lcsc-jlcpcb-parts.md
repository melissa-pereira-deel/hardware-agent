# LCSC and JLCPCB part selection

One file, referenced by both `sourcing-bom` and `manufacturing-dfm`, because
"which part number" is simultaneously a sourcing decision and an assembly cost
line. Keeping it in one place stops the two skills drifting apart.

Checked **2026-09-14**. Fees change; re-check before quoting.

## The three part classes

| Class | What it means | Feeder loading fee |
|---|---|---|
| **Basic** | Permanently loaded on the pick-and-place machines. No feeder swap. | None |
| **Preferred Extended** | Manually loaded, but common enough that JLCPCB waives the fee **on Economic PCBA**. | None on Economic |
| **Extended** | Manually loaded. An operator mounts a feeder for it. | **$3 per unique part number** |

The fee is **per unique part number, not per placement**. Twenty of the same
extended capacitor costs $3 once. Twenty *different* extended parts costs $60
before a single component price.

## What this means in practice

1. **Count unique extended parts and report the total.** It is a real line in
   the quote and it is invisible until you add it up. A BOM summary that omits
   it understates the build cost.
2. **Use Basic parts wherever the exact value is uncritical** — resistors,
   capacitors, common LEDs. This is usually free performance: the part is
   equivalent and the fee disappears.
3. **Check for a Preferred Extended equivalent** before accepting a plain
   Extended part. On Economic PCBA that is a direct $3 saving per part, and the
   classification is not obvious from the part number.
4. **Design against the LCSC library early.** JLCPCB assembly pulls stock from
   LCSC, so a part chosen without checking LCSC availability means a
   re-selection pass later — or a hand-soldered board.

## Stock is a design constraint

- Check **stock and lead time**, not just "in stock". A part on allocation will
  strand you as surely as one that is out of stock.
- Check **lifecycle**. NRND (not recommended for new designs) parts are a
  respin waiting to happen.
- LCSC stock for a given part can be **lower than the quantity you need for the
  panel**. Check against your build quantity, not against 1.

## Where this does not apply

For anything with a **radio, a regulator, or a lithium cell**, buy from an
authorised distributor (DigiKey, Mouser) rather than optimising for the
assembly fee. Counterfeit exposure on those categories costs more than every
feeder fee on the board combined.

---

## Sources

- [JLCPCB — PCB assembly price](https://jlcpcb.com/help/article/pcb-assembly-price) — `trust: high`, checked 2026-09-14
- [JLCPCB — PCB assembly FAQs](https://jlcpcb.com/help/article/pcb-assembly-faqs) — `trust: high`, checked 2026-09-14
- [JLCPCB — when extra charges apply](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra) — `trust: high`, checked 2026-09-14
