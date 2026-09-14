# Sourcing components into Brazil

## Landed cost, not sticker price

```
landed cost = unit price
            + international shipping
            + import duty
            + taxes
            + customs handling / despachante
            + the cost of the delay
```

At prototype quantities the fixed costs dominate, and a part 40% cheaper at LCSC can lose outright to a local distributor once time is priced in. At production quantities the ranking usually flips. Always state which quantity a price refers to.

## Practical constraints

- **LCSC ships to Brazil but requires the consignee's CPF or CNPJ.** The buyer pays duties and taxes on import.
- **Customs delays are real and variable.** Do not put an imported part on the critical path of a demo date without slack.
- **JLCPCB assembly pulls parts from LCSC stock**, which is why designing against the LCSC library early avoids a re-selection pass later.
- **Tax regime is in transition** (CBS/IBS). Treat any specific rate as needing verification rather than quoting it as settled.

## Recommended split

| Situation | Source |
|---|---|
| Prototype, need it this week | Local Brazilian distributor |
| Prototype, can wait 3-4 weeks | LCSC / AliExpress, batched into one order |
| Anything with a radio, regulator, or lithium cell | Authorised distributor (DigiKey/Mouser) - counterfeit risk |
| Production with JLCPCB assembly | LCSC, favouring "basic" parts |

## Batching

Because fixed import costs dominate, batch orders. Keep a running "next order" list rather than ordering per-project. This single habit is usually worth more than any per-part price optimisation at prototype scale.
