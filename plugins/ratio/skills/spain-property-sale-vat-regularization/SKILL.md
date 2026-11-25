---
name: spain-property-sale-vat-regularization
description: >
  When selling Spanish property bought with VAT: how much deducted VAT the
  seller pays back (regularización de IVA, arts. 107-110 LIVA), per unit,
  depending on how the property was used.
metadata:
  version: "1.0.2"
---

# VAT Regularization on Property Sales — Spain

Skill for estimating the VAT a developer must pay back, or may recover, when a property bought with VAT (usually through the waiver of the exemption and the reverse charge) is later sold, whole or unit by unit. Its core is the regularization of investment goods in arts. 107–110 of Ley 37/1992 (LIVA). It covers state rules only.

The typical question: "I bought the building with VAT and deducted it; if I sell this unit under ITP instead of VAT, how much VAT do I have to return?"

## Language

Reply in the language the user writes in, unless they ask for another.
This covers everything the user sees: answers, table headers, reports.
Use the terms and formatting rules in [`references/glossary.md`](references/glossary.md).

## Scope

**Covers:**
- Whether the investment-goods rules apply, based on how the property was used before the sale.
- The pay-back on each exempt sale and the amount in the developer's favour on each subject sale, per unit and in total.
- When the rules do not apply because the property was held only for sale: an explanation and the amount at stake.

**Does not cover, and says so when asked:**
- Deciding the tax regime of each sale (first or second delivery, requirements of the waiver). The regime is an input from the user.
- ITP, AJD or any other tax on the sale, and regional rules.
- The transfer of a whole business (art. 7.1º LIVA, excluded by art. 110.Cuatro).
- Filing: tax forms, deadlines, penalties.

## Rules of behaviour

- **The result is indicative, not tax advice.** Every answer shows the calculation step by step and ends with the points to confirm with a tax advisor.
- **Never assume an input.** If the VAT borne or the deduction percentage is unknown, stop and ask. Do not estimate them from the price.
- **The tax regime of each sale is what drives the result.** State this, and never decide the regime yourself.
- Never name real deals, companies or people in examples. Use the fictitious building in [worked-examples.md](worked-examples.md).

## Methodology

The rules, the formula and their sources are in [rules.md](rules.md). Read it before the first calculation.

### Step 1: Check that the rules apply

Ask two questions, in this order.

**Q1. How was the property used before the sale?**

| Answer | What to do |
|---|---|
| Bought to be sold: maybe refurbished, then sold, never meant to be run as a business | Inventory: the investment-goods rules do **not** apply. Go to Step 1b, which first checks the regime of each sale. |
| Bought to be used in the business, but sold before that use started | Investment good sold before use. Art. 110.Tres applies the art. 110 rules with all ten years remaining, and DGT V5234-26 treats a change of plan before use as a one-off rectification. Both give **100%** of the deducted VAT attributable to the units sold exempt; they differ on the period of the correction. For the exempt units, go to Step 1b for the amount, say that both readings give it, and leave the period to the advisor. Units sold subject to VAT do not take Step 1b's zero: under art. 110.Tres they give an amount in the developer's favour as in Step 3 item 5, with all ten years remaining: allocated VAT borne × (1 − deduction percentage) for each component (Step 2), added up across the components of that sale and then capped once at the VAT charged on it, never once per component; 0 when every component is at 100%. Mark that amount as conditional on the art. 110.Tres reading, and give it in the answer, not in the calculator. |
| Let with an option to buy, still intending to sell | **Conditional.** DGT V0096-12 and V2569-21 treat it as inventory; V3307-17 treats a building built from the start for that letting as an investment good. Ask which case it is. If it was not built or bought specifically for letting with an option to buy, go to Step 1b. If it was, give both results (Step 1b and Steps 2–4 with Q2), mark the answer as conditional, and refer the user to the advisor. |
| Let without an option to buy, run as tourist accommodation, or used in the business | Investment good. Ask Q2. |

**Q2. Was that activity subject to VAT, and in which year did it start?**

| Answer | What to do |
|---|---|
| Subject to VAT (e.g., tourist accommodation with hotel services, business premises let with VAT) | Apply the calculation (Steps 2–4). The period starts in the year the activity started. |
| Exempt (housing let without services) | When the letting started there was a self-supply (art. 9.1º.c LIVA). The VAT of that self-supply was not deductible, so an exempt sale now gives **0** under art. 110. Present this as **conditional** in every case: which VAT is regularized after a self-supply, and from which year, is an open question (see the rules). Ask whether that self-supply was declared; if it was not, that is the main exposure. Either way, refer the user to the advisor and do not calculate further. |

If the user does not know whether the letting carried VAT, explain that it depends on whether hotel-type services were provided, and treat the result as conditional on that answer.

### Step 1b: Property held only for sale

Explain, without applying the art. 110 formula. First ask the regime of each sale, as in every other case: it is an input, never a conclusion of yours.

1. **Sales subject to VAT keep the deduction: nothing to pay back** (art. 94 LIVA). A sale is subject to VAT when it is a first supply, for instance after works that qualify as a refurbishment (art. 20.Uno.22º.B LIVA), or when the exemption on a second supply is waived in favour of a buyer entitled to deduct (art. 20.Dos). If the user does not know the regime yet, show both outcomes for each unit.
2. **Sales that are exempt:** the VAT deducted on the acquisition and on the works and attributable to those units is rectified **in full and in one go**, not spread over ten years:
   - If an exempt sale was already the foreseeable use at the purchase, the deduction was never proper and is corrected in the period of the purchase.
   - If the foreseeable use gave a right to deduct and changed later, it is corrected in the period in which the exempt sale is confirmed.
3. Show the **amount at stake**: the VAT actually deducted and attributable to the units sold exempt only (100%, no reduction for years); units sold with VAT count 0. Label it clearly as "amount at stake", not as a regularization result.
4. Refer the user to the advisor, who must also review the validity of the original waiver and the tax on the purchase.

The calculator does not apply here: its formulas spread the amount over ten years (see Calculator). Give the amount at stake in the answer.

### Step 2: Collect the inputs

Ask for everything that is missing, in one message:

1. **VAT borne** (IVA soportado) on the acquisition, and on any works, as amounts. Not the VAT deducted: the deduction percentage is asked separately. If the user only knows the VAT deducted and the percentage, VAT borne = VAT deducted ÷ percentage.
2. **Deduction percentage** (prorrata) of the year the VAT was borne. 100% if the company only carries out operations with a right to deduct.
3. **First year of the period**: the year the property started to be used (Q2), if later than the acquisition.
4. **Allocation** of the VAT borne among the units, or its basis (surface, price, participation coefficient).
5. **For each sale**: unit, date, tax regime (subject to VAT, or exempt and taxed under ITP) and, for sales subject to VAT, the VAT charged on the sale. The VAT charged is **required** when the deduction percentage is below 100%: without it the cap cannot be applied.
   "VAT charged" means the VAT due on that sale. When the sale goes under the reverse charge (art. 84.Uno.2º.e LIVA, typically a waived exemption), the invoice shows no VAT and the buyer self-assesses it: use that VAT due as the cap, and mark the result as conditional, naming the open question on the cap under the reverse charge. Never use 0 because the invoice shows none.

Two cases make the result conditional. Say so in the answer, and name the matching open question from the rules among the points to confirm:

- **Works VAT is a significant part of the VAT borne.** VAT on works borne after the acquisition is regularized from the same start date, per year elapsed (art. 107.Cuatro), and may have been deducted with a different percentage. Ask for acquisition VAT and works VAT separately, with the year and the percentage of each. If the percentages or the periods differ, calculate each part on its own and add them up (for the spreadsheet, one copy per part: see Calculator).
- **Use started after the acquisition.** The percentage applied at the purchase may have been provisional (art. 105 LIVA). Ask whether the percentage given is the provisional one or the definitive one, and if the user does not know, state which one you used.

### Step 3: Calculate

For each unit:

1. Allocated VAT borne = VAT borne × unit's share of the allocation basis.
2. Last year of the period = first year + 9.
3. Remaining years = last year − year of the sale + 1, between 0 and 10. **The year of the sale counts in full.** A sale after the period gives 0.
4. **Exempt sale:** to pay back = allocated VAT borne × deduction percentage ÷ 10 × remaining years.
5. **Subject sale:** in the developer's favour = allocated VAT borne × (1 − deduction percentage) ÷ 10 × remaining years, capped at the VAT charged on that sale. With a 100% percentage, this is 0.

Round each unit to cents and add up the totals. Check your arithmetic against the matching case in [worked-examples.md](worked-examples.md).

### Step 4: Answer

Follow [output-template.md](output-template.md).

## Calculator

The skill bundles a spreadsheet with visible formulas and the worked examples, one sheet each:

- [assets/calculadora-regularizacion-iva.xlsx](assets/calculadora-regularizacion-iva.xlsx): Spanish labels, for replies in Spanish or Catalan.
- [assets/vat-regularization-calculator.xlsx](assets/vat-regularization-calculator.xlsx): English labels, for any other language.

When the user wants the spreadsheet, or has more than a handful of units:

**Only investment goods (Steps 2–4).** The formulas apply the art. 110 fraction (÷ 10 × remaining years), so property held only for sale (Step 1b) never goes in the calculator: its amount at stake is 100% of the attributable VAT deducted, with no reduction for years. In a conditional case with both results (Q1), fill the calculator only for the investment-good result and give the Step 1b amount in the answer.

**One copy per component.** The calculator holds a single deduction percentage (B5) and a single first year (B6). If the VAT borne has parts with different percentages or different regularization periods (for example acquisition and works, see Step 2), fill **one copy per part**, each with its own VAT borne, percentage and first year, name the files after the part (e.g. "…-acquisition.xlsx", "…-works.xlsx"), and give the total of all parts in the answer. A different year in which the VAT was borne, with the same period and percentage, is not a separate part. Never force two percentages into one sheet.

The cap on a subject sale applies once per sale, not once per copy. For each subject sale, work out each part's amount in favour without the cap, then enter in column G of each copy that sale's VAT charged split in proportion to those uncapped amounts. The copies then add up to the uncapped total when it is below the VAT charged, and to exactly the VAT charged when it is above. Never enter the full VAT charged in more than one copy.

**If you open or fill the calculator in a conversation, always hand the filled copy to the user, even if they did not ask for it.** Never use it only to compute: the file is part of the answer. Say in the answer which file it is and that it shows the same figures.

1. Copy the right file to the outputs folder. Never edit the bundled one.
2. Open the copy with `openpyxl.load_workbook(path, data_only=False)`, so the formulas survive. Never use `pandas` or `data_only=True`: they lose the formulas.
3. Fill in only the yellow input cells of the first sheet: B4 VAT borne, B5 deduction percentage, B6 first year, and from row 11 down columns A (unit), B (allocation basis), E (sale date), F (regime, exactly as in the dropdown), G (VAT charged on subject sales). It holds up to 100 units, one per row. Never insert rows: the totals would not cover them.
   With a deduction percentage below 100%, column G is required on every subject row: a blank one shows "missing VAT charged" and is left out of the total.
4. openpyxl does not recalculate. Compute the results yourself as in Step 3, report them in the answer, and tell the user the file will show the same figures when opened in Excel.
5. Hand the filled copy to the user. Keep any helper script or environment out of the outputs folder: the user should find only the spreadsheet there.

**More than 100 units.** Group units into one row only when they share the year of sale and the regime, entering the sum of their allocation bases and a unit label that names them all (e.g., "U1–U25"). The result is the same as unit by unit, up to a few cents of rounding, because the formula is linear in the allocated VAT. Two limits:

- Sales subject to VAT with a deduction percentage below 100%: the cap applies to each sale's own VAT charged, so a summed cap can give a different result. Group them only if no sale in the group reaches its own cap (its amount in favour is below its VAT charged); then enter the sum of their VAT charged in column G. If any sale reaches its cap, give it its own row.
- Never group units sold in different years: each year has its own remaining years.

If the rows still do not fit, do not hand over a spreadsheet. Give the calculation in the answer, grouped by year and regime as in Step 3, and tell the user why there is no spreadsheet.
