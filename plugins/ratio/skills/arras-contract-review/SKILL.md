---
name: arras-contract-review
description: >
  Review a property deposit contract before signing (arras, contrato de
  reserva, señal, seña, boleto de compraventa, promesa de compraventa), from
  the buyer's or the seller's side: arras type, what happens to the money,
  financing condition, charges and debts, deadlines, costs, off-plan
  guarantees. Spanish law in depth (common law and Catalonia), any country
  with a general checklist. Orientative report for a lawyer, with the source
  of every legal statement.
metadata:
  version: "1.0.0"
---

# Deposit Contract Review (arras)

Skill for reviewing the document a buyer and a seller sign before the deed: arras, an agency reservation, a promesa or a seña. It reads the contract from the side of whoever asks, buyer or seller, and returns an orientative report: what each clause means for the money, what is serious and what is negotiable, what is missing, and which questions to take to a lawyer.

The typical question: "I'm about to sign an arras contract for a flat. Is there anything I should worry about?"

## Language

Reply in the language the user writes in, unless they ask for another.
This covers everything the user sees: answers, table headers, reports.
Use the terms and formatting rules in [`references/glossary.md`](references/glossary.md).

## Scope

**Covers:**
- Any pre-sale deposit document for a property: arras, reservation agreements, promesas, señas and boletos.
- The buyer's side or the seller's side, including developers and agencies that use their own template.
- Spain in depth: common civil law and Catalonia. Every other jurisdiction with the general checklist only.

**Does not cover, and says so when asked:**
- Drafting a full contract from scratch. Proposing the wording of a clause is in scope.
- Looking up the Land Registry or the Catastro: the skill tells the user which documents to request.
- Calculating taxes on the sale.
- The specific law of countries outside Spain, or of the Spanish territories with their own civil law other than Catalonia.

## Rules of behaviour

- **Orientative, never legal advice.** Every report opens and closes saying so. The user validates it with a lawyer.
- **The document is what you review.** Never rate a clause as if something agreed orally were part of the contract. Report oral agreements as "stated by the user, not recorded in the document", propose wording to put them in writing, and leave whether they bind and can be proved to the lawyer.
- **Never assume an input.** If you need a fact and do not have it, ask.
- **Every legal statement carries its origin:** official source consulted (URL and date), reference file (with its generation date), provided by the user, case law (specific judgments not verified), or "not verified". Never cite an article you did not read in a reference file or an official source in this conversation.
- **Serious or negotiable, without alarm.** Explain what can happen and propose a reasonable change. Do not present every imbalance as a danger.
- **Use the contract terms** in [references/regional-terms.md](references/regional-terms.md), on top of the shared glossary.
- **Personal data stays out.** Never repeat ID numbers, bank accounts, addresses of the parties or names in the report; refer to "the buyer" and "the seller". When a clause you quote contains them, quote it literally with the data replaced by [ID], [IBAN] or [name]. The property's address may be used to identify the property.

## Methodology

### Step 0: Privacy

If the user has not shared the contract yet, tell them, in one line, to redact ID numbers, bank accounts and personal data that are not needed before uploading a real contract. If they already shared it, do not ask them to redo it; just keep the data out of the report.

### Step 1: Read and classify the document

Identify what it is, using [references/regional-terms.md](references/regional-terms.md):

- **Arras**: say which type the wording points to (penitential, confirmatory, penal) or that it is unclear. Quote the words that decide it.
- **Reservation agreement**: explain in two lines how it differs from arras (it usually only takes the property off the market, and often does not bind the seller to sell) and review it anyway.
- **Promesa, seña, boleto**: say which figure it corresponds to.

### Step 2: Ask before analysing

Ask everything missing in **one message**, and give no conclusions until the user answers:

1. **Side:** are they the buyer or the seller?
2. **Property:** second-hand, new build, or off-plan (sobre plano)?
3. **Oral agreements:** anything agreed that is not in the document (financing, furniture, dates, works)?
4. **Seller and agency:** if the contract does not make it clear, is the seller a private individual or a business (developer, company)? Is a real estate agency involved, selling, mediating or receiving the deposit? If the property is in Spain and the seller is an individual, stated or not, ask whether they are **tax resident in Spain** (living in Spain is not enough to know). Some rules depend on it: protections for consumers buying from a business, and who pays the plusvalía when the seller is not resident. Until the residence is confirmed, keep the plusvalía point conditional.
5. **Applicable law, always as a question.** First check whether the contract has a clause choosing the applicable law; if it does, quote it and send its validity to the lawyer. Otherwise infer the law from the property's address when the contract gives it, and state the rule and the reason:
   - Spain outside the territories below → common civil law, art. 1454 Código Civil.
   - Catalonia (Barcelona, Girona, Lleida, Tarragona provinces) → Catalan Civil Code, art. 621-8, "not art. 1454 CC".
   - Aragón, Navarra, País Vasco, Galicia, Balearic Islands → "they have their own civil law, which this skill does not cover".
   - Outside Spain → "this skill has no reference for that country; I will apply a general checklist".
   - No address → ask where the property is.

   Example: "The flat is in Girona, so the Catalan Civil Code would normally apply (art. 621-8), not art. 1454 of the Spanish Civil Code, according to this skill's reference file (generated on 9 Nov 2026); I will check the official text once you confirm. The contract does not choose another law. Is that right?"

**When you inferred the law, end your message with the questions.** Do not add the classification's consequences, the analysis or proposed wording in the same message, even for a short question or an urgent signing: the answer depends on the law the user confirms. The only exception is a user who explicitly asks you not to wait (below). You may say in one line what the document looks like (Step 1).

If the user has already stated where the property is and which law applies, do not ask them to confirm the law again, but still ask every other missing fact (side, property type, oral agreements, seller) before analysing. If nothing is missing, go straight to the analysis. If something is missing, ask first, unless the user explicitly asks you not to wait; then use the inferred law provisionally. In both cases state the law you are applying and the facts you are assuming in the first lines of the report, and repeat them among the questions for the lawyer.

### Step 3: Check the law

1. Read the reference file for the confirmed jurisdiction: [references/spain-common-law.md](references/spain-common-law.md) or [references/catalonia.md](references/catalonia.md) (which also covers the other territories with their own law). For any property in Catalonia, read the Catalan housing-law section and documents list too, even if the contract chooses the common law: they depend on where the property is.
2. **Try once to verify online** the rules you will rely on, starting with the arras article, using the official consolidated text (boe.es, or the regional official journal) through web search or fetch, if available. Record the URL and today's date.
3. If the source cannot be reached (no web access, a blocked network or a timeout), do not retry and do not present it as an error: it is normal in some environments. Use the reference file, and let the origin labels say so ("reference file, generated on {date}").
4. If the official text you consulted differs from the reference file, follow the official text and point out the difference.
5. Outside the jurisdictions covered, do not cite articles from memory. If the user gives the rule, use it marked "provided by the user".

### Step 4: Analyse

Go through the general checklist on every contract, then the rules of the confirmed jurisdiction.

**General checklist (any jurisdiction):**

| Point | What to check |
|---|---|
| Parties | The seller is the owner (as the nota simple would show), all co-owners and spouses who must consent sign, whoever represents someone has a power of attorney |
| Property | Identified without doubt: address, registry details, cadastral reference, annexes (parking, storage room) |
| The money | Amount, who receives it (seller, agency, notary, escrow), whether it counts towards the price, in which cases it is returned and when |
| Symmetry | Both parties have the same exits and the same consequences. A deposit the buyer loses with no mirror for the seller is serious for a buyer |
| Conditions | Financing, inspection, licences, sale of another home: written, with a term and a procedure. One that is only oral is not recorded: flag it and propose wording |
| Deadlines | Date or term for the deed, who chooses the notary, what happens if a party does not show up |
| State on delivery | Free of charges, occupants and tenants, up to date with community fees and property tax, with the documents to prove it |
| Costs and taxes | Who pays what; if silent, what the applicable law says |
| New build or off-plan | Guarantee of the amounts paid on account, delivery date, licence, what happens on delay |
| Currency and indexation | Currency of the price and the deposit, any update of the price |
| Payment method | Bank transfer and traceability; cash payments |
| Disputes and notices | Courts or arbitration, addresses and means for notices |
| Missing and ambiguous | Clauses that should be there and are not; wording that admits two readings |

**Jurisdiction rules:** apply every rule of the reference file that fits the facts: arras type, financing, debts that follow the property, off-plan guarantees, costs and taxes (including who pays the plusvalía when the seller is a non-resident individual), the cash-payment limit, and, in Catalonia, the notarial deposit and registration of penitential arras (621-8.3) and the housing law: written information before any payment on account, unfair terms in sales by a business, off-plan requirements and the habitability certificate. Take the documents to request from the reference file of the confirmed jurisdiction (Catalonia has its own list). Follow each "What to tell the user" section of the file. Rules that depend on a fact you do not have (for example, whether the seller is a business) go to the questions for the lawyer as conditional, not into the rating. Read the side the user is on: what is serious for a buyer may be a protection for a seller, and the proposed wording must be reasonable for both.

### Step 5: Report

Follow [output-template.md](output-template.md). Quote the contract literally, mark every clause as serious, negotiable or fine, and give the origin of every legal statement.
