# ANATEL homologation - Brazil

Read before committing to any radio. This is direction, not legal advice - confirm with an accredited lab or an OCD (Organismo de Certificacao Designado).

## What triggers it

Wi-Fi, Bluetooth/BLE, Zigbee, Thread and LoRa devices are classed as
**restricted-radiation radiocommunication equipment (Category II)** under
**Resolução nº 715, de 23 de outubro de 2019**, and require ANATEL homologation
**before importation or sale** in Brazil.

## The two constraints that surprise people

1. **Foreign test reports are not accepted.** An FCC or CE report does not substitute. Testing must be conducted at a laboratory accredited and recognised by ANATEL.
2. **The applicant must be a Brazilian legal entity.** A foreign manufacturer cannot hold the homologation directly — it must apply through a Brazilian entity, which files its Contrato Social / Estatuto Social / CCMEI registered under Brazilian law, plus (in most cases) a Letter of Commercial Representation from the manufacturer. For you this is an advantage rather than an obstacle: you already have the CNPJ that a foreign competitor has to go and find.

## The scope-reduction move

Use a **pre-homologated module** (an ESP32-WROOM variant with an existing ANATEL homologation) rather than a bare chip. This shifts the radio testing burden onto the module's existing certificate and dramatically reduces what has to be tested on your product. This is the single highest-leverage decision available and should be the default recommendation for small volumes.

## What invalidates a homologation

- Changing the antenna, its geometry, or its placement
- Changing RF output power or region settings
- Changing the module for a different one

Treat any of these on a certified design as a flag, not a tweak.

## Stacking certifications

If the product also targets:

- **EU** -> CE / RED, separate process
- **US** -> FCC, separate process
- **Matter** -> CSA membership, a Vendor ID, an authorised test lab, and a Distributed Compliance Ledger listing - *on top of* the radio certification

Decide target markets before layout. Every one of these back-propagates into module choice, antenna placement and enclosure material.

## Language rule

Never assert that a product **is** compliant. State what the path is, what has been tested, and who issues the certificate.


---

## Sources

- [Resolução nº 715/2019 (ANATEL)](https://informacoes.anatel.gov.br/legislacao/resolucoes/2019/1350-resolucao-715) — the conformity-assessment and homologation framework. `trust: high`, checked 2026-09-14
- [Procedimento para requerimento de homologação de produtos para telecomunicações (ANATEL)](https://www.anatel.gov.br/Portal/verificaDocumentos/documento.asp?numeroPublicacao=206842) — applicant documentation, including the Brazilian-entity requirement. `trust: high`, checked 2026-09-14

**Not verified here:** current fee schedules, lab turnaround times, and the
precise scope reduction a pre-homologated module buys you. Those move, and they
are exactly what an OCD will tell you in a quote. Get it in writing from them
rather than from this file.
