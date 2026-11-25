---
name: spain-tax-auction-search
description: Search the properties the Spanish Tax Agency (AEAT, Hacienda) auctions, by place, type, price and charges. Use for "subastas de Hacienda", AEAT auctions or buying at auction in Spain.
metadata:
  version: "1.0.1"
---

# Spanish Tax Agency Auction Search

Search the properties the AEAT is auctioning (homes, commercial units, garages, storage rooms, plots, rural land), using the official list it publishes every day, and tell the user what a non-expert misreads in each one.

The bundled script does every read: downloading, finding, filtering, counting and exporting the list. **Never read, filter or summarise the list file yourself, and never use web fetch or web search to get it**: they return a summary, not the records.

## Language

Reply in the language the user writes in, unless they ask for another.
This covers everything the user sees: answers, table headers, reports.
Use the terms and formatting rules in [`references/glossary.md`](references/glossary.md).

## The tool

`scripts/aeat_auctions.py`, inside this skill's directory. Python 3.10+, standard library only. Run it with `python3 <skill dir>/scripts/aeat_auctions.py <command>`. Every command prints JSON; on failure it prints `"ok": false` with a stable `error` code and exits 2.

| Command | What it does |
|---|---|
| `fetch` | Tries to download the list into a cache. Never downloads twice on the same day |
| `locate [PATH ...]` | Finds the newest copy on disk by its content, whatever its name (`bienes (1).js`, `bienes.js.txt`, a Safari web archive...) |
| `search [filters]` | Open auctions matching the filters. Already closed ones are discarded |
| `show ID` | Full record: description, photos, GPS, AEAT and BOE links. `ID` is a property id, or a `SUB-AT-...` auction id, which returns every lot of that auction |
| `stats [filters]` | Counts, properties without charges and valuation ranges by province and by type |
| `export --out PATH [filters]` | Writes every match to `PATH`, `.csv` or `.xlsx` |

Filters (for `search`, `stats` and `export`): `--provincia` (name, Basque/Catalan/Galician name, or INE code), `--municipio` (part of the name), `--cp`, `--tipo` (vivienda, local, garaje, trastero, nave, solar, finca, otros; repeatable or comma-separated), `--solo-pleno-dominio` (full ownership of 100 %), `--precio-min`, `--precio-max` (on the valuation, EUR), `--sin-cargas`, `--cargas-max`, `--cierre-hasta YYYY-MM-DD`, `--con-ref-catastral`, `--texto` (part of the description or address), `--orden cierre|valoracion|cargas|neto`, `--desc`. `search` also takes `--limit` (default 20) and `--compact` (one short record per property: use it for lists; use `show` for detail). `--file PATH` uses a given copy instead of the newest found.

## Workflow

### 1. Get the list

Go down this list and stop at the first step that works:

1. **`fetch`.** Some organisations allow the AEAT's domain. `network_blocked` or `network_timeout` is normal in a sandbox: do not mention it to the user as an error, go to the next step.
2. **`locate`.** It looks in the connected folders (`~/mnt/*`), in the files the user uploaded (`/mnt/user-data/uploads`), in the fetch cache, the working directory and home. If the user told you where the file is, pass that path.
3. **If you can see the user's own folders** (a Downloads folder, the desktop) but `locate` did not find the file, look there for a file named like `bienes*`, copy it into the sandbox, and run `locate` again on the copy.
4. **Only then, ask the user.** Briefly, in their language, the link first:

   > Open this link: <source_url>. Your browser will probably show a page full of text. That's expected: that text is the list. Save it with **⌘S** (Mac) or **Ctrl+S** (Windows) into your connected folder, or drag the saved file into this chat. Tell me when it's done.

   Add these only when they apply:
   - **Before opening it:** right-click the link → "Save link as…" (Chrome, Firefox, Edge) or "Download linked file" (Safari). On a Mac, ⌥-click downloads directly in Safari and Chrome.
   - **Safari asks for a format:** choose "Page source", not "Web archive".
   - **Nothing else works:** select all the text (⌘A / Ctrl+A), copy it and paste it into the chat. If it arrives as a file, run `locate` on it; if it arrives as text, save it to a file first and pass that path.
   - **To make it a single click next time:** connect the Downloads folder; the browser then saves the list straight into it.

   When the user says it is done, run `locate` again.

Then check the date. `age_days` 0 or 1: go on. Older: tell the user the date of their list, that auctions close and appear every day, and let them choose between going on with it or downloading a fresh one. `age_days` null means the copy carries no date (a partial copy or paste, for example): never present it as current. Ask for a fresh download; if the user prefers to go on, say above the results that the date of the list is unknown and some auctions may have closed.

If a command returns `truncated`, the download was cut: ask for it again. `format_changed` means the AEAT changed its file: say so plainly and stop; do not try to read the file another way.

### 2. Search

Translate the request into filters. Ask only when a missing piece changes the answer a lot (no place at all, for example). "Sin cargas" is `--sin-cargas`; a budget is `--precio-max` on the valuation. Start broad, then narrow.

- **No matches:** say which filter emptied the list. When the place is what emptied it, `search` returns `provincias_con_subastas`: suggest the nearby provinces **from that list only**, with their counts. Never name a province with open auctions that is not in it.
- **Overview questions** ("¿qué hay en subasta?", "¿dónde hay más?"): use `stats`, not a long `search`.
- **A spreadsheet:** use `export`, with the output in the user's connected folder (or `/mnt/user-data/outputs` in the cloud) so they can open it.

### 3. Present

- **A table** with: type, municipality, valuation, charges, net (valuation minus charges), closing date and the link to the AEAT record (`url_aeat`). Above it, how many matched, how many are shown, and the date of the list.
- **`show`** for the properties the user cares about: description, photos (`fotos`), GPS and the BOE auction (`url_boe`). If `subasta_cerrada` is true, say first that this auction has already closed: the list in use is older than its closing date.
- **Always end with the attribution line**, exactly as the JSON gives it (`atribucion`). The data is licensed CC BY 4.0 and the attribution is mandatory and must be visible.

### 4. Warn about what non-experts miss

Each result carries `avisos`. Explain each one that applies, next to the property it applies to:

- **`derecho_no_pleno`**: the right auctioned is not full ownership. Explain what the buyer actually gets, by the value of `derecho` (table below).
- **`titularidad_parcial`**: only `porc_titularidad` % of the right is auctioned. The buyer becomes a co-owner with the other holders: they share the use and any sale or rental needs agreement among them, or a court case to divide the property. The valuation is of that share, not of the whole property.
- **`con_cargas`**: prior charges (`cargas_eur`) that the buyer takes on. Compare properties by the net figure, not by the valuation.
- **`posible_multipropiedad`**: the description reads as a timeshare: the use of the property for some weeks a year, not the property. The AEAT may still record it as full ownership of 100 %. Quote the words of the description that show it, and present it as a timeshare week, not as a home.

What each right gives the buyer:

| `derecho` | What the buyer gets |
|---|---|
| Pleno dominio | Full ownership: the buyer can use, rent and sell the property. |
| Nuda propiedad | Ownership without use. Someone else, the usufructuary, keeps living in it or renting it out and collects the rent, and usually pays the IBI and the ordinary upkeep. The buyer gets the use only when the usufruct ends, usually when the usufructuary dies, a date nobody can know. The younger the usufructuary, the longer the wait. |
| Usufructo | The use without ownership: living in it or renting it out, for as long as the usufruct lasts. A bought usufruct still ends when it would have ended for the original holder, usually at that person's death. The buyer can lose it at any moment and gets nothing back. They cannot sell the property, must keep it in good condition, and usually pay the IBI and the ordinary upkeep. |
| Leasing (opción de compra) | The debtor's place in a leasing contract. The property stays owned by the leasing company, usually a bank. The buyer can use it while paying the remaining instalments, and can buy it at the end by paying the purchase option. The pending instalments and the option price are on top of the auction price: they are in the auction's conditions on the BOE. |
| Derecho de superficie | The right to own a building on land that belongs to someone else, for a fixed term. When the term ends, the building passes to the owner of the land. The remaining years are what the right is worth. |
| Derechos hereditarios | The debtor's share in an inheritance that has not been divided yet. The buyer takes the heir's place, not a specific property. What they end up with depends on the division agreed with the other heirs, or decided by a court, and may be a part of several assets. |
| Otros | A mix or a right not listed above. The description says what it is, often in its first words ("50% PLENO DOMINIO Y 16,66% USUFRUCTO"): explain each part. |

The first words of `descripcion` usually state the right and the share as registered ("25% DE NUDA PROPIEDAD", "100 % DEL DERECHO DE USO EN RÉGIMEN DE APROVECHAMIENTO POR TURNOS"). When they disagree with `derecho` or `porc_titularidad`, tell the user, quote both, and tell them to check the auction's documents on the BOE before bidding. Do not pick one.

Whenever a result carries `derecho_no_pleno`, `titularidad_parcial` or `posible_multipropiedad`, say the user should have the auction's documents checked by a lawyer before bidding.

And whenever results are shown:

- **The valuation is the AEAT's appraisal for the auction**, not a market price.
- **Bids are placed on the BOE's auction portal** (`url_boe`), with a deposit; the conditions are there. You cannot open these links from the sandbox, but the user can.

## Limits

- Only AEAT auctions, only real estate, only those currently open. Judicial and notarial auctions are not in this list.
- The data is as fresh as the copy of the list in use; the AEAT publishes a new one every day around 15:00.
- No BOE details (deposit, minimum bid, documents): the BOE portal has no API, and the user must check them there.
