# Rules: regularization of investment goods on sale

State law only. Every figure below carries its source and the date its wording came into force. Last checked against the BOE, DGT and TEAC on 23 Sep 2026.

## Law

Ley 37/1992, del Impuesto sobre el Valor Añadido (LIVA), consolidated text: https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740

| Rule | Article | In force since | Source |
|---|---|---|---|
| Only investment goods are regularized: goods that, by nature and function, are normally used for more than one year as instruments of work or means of operation | 108.Uno | 01/01/1993 (original wording) | [art. 108](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a108) |
| Land and buildings: 10-year period, the year of acquisition plus the nine following calendar years. If use starts later, the year use starts plus the nine following | 107.Tres | 28/05/1993 (RDL 7/1993) | [art. 107](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a107) |
| The annual difference is split into tenths for buildings | 109.3º | 01/01/1993 (original wording) | [art. 109](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a109) |
| Sale within the period: one single regularization for the rest of the period | 110.Uno | 01/01/1993 (original wording) | [art. 110](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a110) |
| Subject and not exempt sale: 100% deductible "durante todo el año en que se realizó dicha entrega y en los restantes"; the extra deduction cannot exceed the VAT charged on the sale | 110.Uno.1º | 01/01/1993 | [art. 110](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a110) |
| Exempt or non-subject sale: 0% deductible for the whole year of the sale and the rest of the period | 110.Uno.2º | 01/01/1993 | [art. 110](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a110) |
| Applies even without a pro rata in earlier years, and without the 10-point threshold of art. 107 | 110.Dos | 01/01/1993 | [art. 110](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a110) |
| Applies also if the good is sold before being used | 110.Tres | 01/01/1993 | [art. 110](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a110) |
| Never applies to the transfer of a whole business | 110.Cuatro, 7.1º | 01/01/1993 | [art. 110](https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a110) |

## Formula

Art. 109 compares, for each remaining year, the deduction made in the year the VAT was borne with the deduction that the new percentage would give, and divides the difference by ten:

```
per year        = (VAT borne × initial %  −  VAT borne × new %) ÷ 10
exempt sale     : new % = 0    →  pay back  = VAT borne × initial % ÷ 10 × remaining years
subject sale    : new % = 100  →  in favour = VAT borne × (1 − initial %) ÷ 10 × remaining years
                                              capped at the VAT charged on the sale
remaining years = last year of the period − year of the sale + 1   (0 after the period)
```

The percentage applies to the **VAT borne**, not to the VAT deducted. Multiplying the VAT deducted by the percentage counts it twice.

**Official check.** AEAT, [Manual práctico de IVA 2025, ch. 5](https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/manual-iva-2025/capitulo-05-deducciones-devoluciones/deducciones/regularizacion-deducciones-bienes-inversion/entregas-bienes-invers-per-regularizacion.html):

- Building bought in "n-1" with 420,000 of VAT, deduction percentage of 50%, exempt sale in "n": 420,000 × 50% = 210,000, and (210,000 ÷ 10) × 9 = **189,000** to pay back.
- The manual adds: «se multiplica por 9, porque son los años que faltan para que termine el período de regularización, computándose a estos efectos el año en que se produce la transmisión».

## When the rules apply

Researched on 23 Sep 2026 in the texts of the binding rulings (DGT), TEAC doctrine and the AEAT manual. What decides is **the use given to the property**, not the accounts.

| Use before the sale | Classification | Consequence of an exempt sale | Sources |
|---|---|---|---|
| Bought to be sold | Inventory | No art. 110. The deduction is rectified in full and in one go (arts. 99.Dos and 114). If an exempt sale was foreseeable from the start, the correction goes to the period of the purchase | TEAC 00/04281/2021 (20/02/2024), following CJEU C-532/16; DGT V1621-25 (15/09/2025) |
| Bought for use in the business, sold before that use started | Investment good sold before use | Two readings, same amount: art. 110.Tres applies art. 110 with all ten years remaining (10/10 = 100%); the DGT treats a change of plan before use as a one-off rectification of 100% (arts. 99.Dos and 114). They differ on the period of the correction: to the advisor | Art. 110.Tres LIVA; DGT V5234-26 (22/07/2026), following CJEU C-791/18 |
| Let with an option to buy, still intending to sell | Inventory, **conditional** | Same as "bought to be sold", unless the building was built from the start for that letting, which the DGT has treated as an investment good | DGT V0096-12 (20/01/2012), V2569-21 (21/10/2021); contra V3307-17 (28/12/2017) |
| Let without an option to buy, or run as a business | Investment good | Art. 110 | DGT V0096-12, V2569-21 |
| From inventory to exempt housing letting | Self-supply under art. 9.1º.c): the self-assessed VAT is not deductible | Art. 110 gives 0 on an exempt sale | DGT V1334-16 (31/03/2016) |
| From inventory to an activity subject to VAT | No self-supply (no separate sector: percentages do not differ by more than 50 points) | Art. 110 on the original VAT borne | TEAC 00/01471/2019 (20/01/2022), criterion not yet repeated |
| Works that qualify as a refurbishment (art. 20.Uno.22º.B) | — | The sale is a first supply, subject to VAT: nothing to pay back | DGT V5234-26 |

- The period starts when use actually starts. The DGT accepts the start of marketing of the whole property as a reasonable date (V3307-17, 28/12/2017).
- Rulings can be looked up by number in the DGT database: https://petete.tributos.hacienda.gob.es/consultas/

## Open questions for the advisor

Not settled by the sources above. List the ones that affect the user's case at the end of every answer.

- **Land.** Whether the land portion follows the same period. Art. 107.Tres treats "terrenos o edificaciones" alike.
- **Refurbishment.**
  - VAT on works borne after the acquisition is regularized from the same start date, per year elapsed (art. 107.Cuatro). How this combines with a sale mid-period is to be confirmed.
  - When the period starts if the building was refurbished before use.
- **Minimum letting period.** No source fixes how long a letting must last to turn inventory into an investment good.
- **Tourist letting.** Whether it was subject to VAT depends on hotel-type services. No specific ruling for developers was found.
- **Letting with an option to buy.** V3307-17 treats a building built for it as an investment good; V0096-12 and V2569-21 treat it as inventory.
- **After a self-supply.** Which VAT is regularized (the self-assessed one or the original one) and from which year.
- **Allocation.** How to split the building's VAT among units sold in different years. Surface, value or participation coefficient are reasonable, but none is set by law.
- **Earlier annual regularizations** under art. 107, if the deduction percentage changed before the sale.
- **Which percentage is the initial one** when use starts after the acquisition: the provisional percentage of the year of purchase, or the final one of the year use starts (art. 105 LIVA).
- **The waiver of the exemption** on the purchase, and the risk of ITP if the buyer never had a right to deduct.
- **The cap on subject sales** when the sale itself goes under the reverse charge.
- **Rounding.**
- **Investment good sold before use, subject sales.** Art. 110.Tres gives an amount in favour with all ten years remaining when the initial percentage is below 100%; V5234-26 only addresses exempt sales, so whether that amount is accepted under the one-off rectification reading is to be confirmed.
- **V5234-26 is recent** (July 2026). Check whether later rulings qualify it.
