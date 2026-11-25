---
name: spain-cadastral-lookup
description: >
  Look up cadastral data (referencia catastral, datos catastrales) for any
  property in Spain using the public Catastro API. Returns official property
  characteristics: cadastral reference, built surface, year of construction,
  participation coefficient, use classification, and building unit count.
  Works across Spain except the foral territories (Álava, Gipuzkoa, Navarra,
  Bizkaia). Activate when the user
  asks about "referencia catastral", "datos catastrales", "Catastro", or wants
  to look up official property registry information.
allowed-tools: WebFetch
metadata:
  version: "1.0.2"
---

# Cadastral Lookup — Spanish Catastro

Skill for looking up official cadastral data from the Dirección General del Catastro. Covers every province and municipality of Spain except the foral territories — Álava, Gipuzkoa, Navarra and Bizkaia — which keep their own cadastres. For an address there, say that the Catastro does not hold it and point the user to that territory's own cadastre.

## Language

Reply in the language the user writes in, unless they ask for another.
This covers everything the user sees: answers, table headers, reports.
Use the terms and formatting rules in [`references/glossary.md`](references/glossary.md).

## Modes of Use

### Mode 1: Unit Lookup (by address)

The user provides a **province**, **municipality**, **street address**, **floor**, and **door**. Return the cadastral data for that specific unit.

Examples of user input:
- "Datos catastrales de calle Praga 14, entresuelo 1a, Barcelona"
- "Referencia catastral de Avenida de la Constitución 3, planta 2, puerta B, Sevilla"
- "Cadastral info for calle Alcalá 50, 3rd floor, door 1, Madrid"

### Mode 2: Building Lookup (by address)

The user provides a **province**, **municipality**, and **street address** without specifying floor and door. Return the building-level data with a directory of all units.

Examples of user input:
- "Cuantas viviendas tiene el edificio de calle Praga 14, Barcelona?"
- "Building units at Gran Via 100, Madrid"
- "Datos del edificio en Rambla Catalunya 50, Barcelona"

### Mode 3: Lookup by Cadastral Reference

The user provides a **cadastral reference number** directly. Return the property data for that reference.

- If the reference is **20 characters** (unit-level), return unit data plus building context (same as Mode 1).
- If the reference is **14 characters** (plot/building-level), return building data with the Unit Directory (same as Mode 2).

Examples of user input:
- "Buscar referencia catastral 0251804DF3805A0003TH" (20 chars → unit)
- "Datos del inmueble con RC 0143706DF3804C" (14 chars → building)
- "Datos del edificio con referencia 9872023VH5765A" (14 chars → building)

## Methodology

Follow these steps in order:

### Step 1: Identify province and municipality

Determine the province and municipality from the user's input.

- If the user explicitly names them, use those values directly.
- If the user names only a city (e.g., "Barcelona", "Madrid"), use the city name as both province and municipality — this works for most major cities where province and city share the same name.
- If the location is ambiguous (e.g., a small town that could be in multiple provinces), use the ConsultaProvincia and ConsultaMunicipio endpoints to resolve. See [`references/catastro-api.md`](references/catastro-api.md) for details.
- If you cannot determine the province/municipality, ask the user.

### Step 2: Parse the address

From the user's input, extract:

1. **Street type (Sigla)**: map the user's street type to the Catastro code using the Sigla table in [`references/catastro-api.md`](references/catastro-api.md). Default to `CL` (Calle) if the user provides a bare street name.
2. **Street name**: the name without the type prefix (e.g., "PRAGA" from "calle Praga").
3. **Number**: the street number.
4. **Floor (Planta)**: map to Catastro floor codes (0 for the ground floor, EN, PR, 01, 02, etc.). See the floor code table in the API reference. If the unit is not found, use the listing fallback it describes rather than guessing another code.
5. **Door (Puerta)**: pass as-is.

### Step 3: Call the Catastro API

Use WebFetch to call the appropriate endpoint:

- **Modes 1 and 2**: use `Consulta_DNPLOC` with the parsed address components. For Mode 1, include Planta and Puerta. For Mode 2, leave them empty.
- **Mode 3 (unit reference, 20 chars)**: use `Consulta_DNPRC` with the full reference.
- **Mode 3 (building reference, 14 chars)**: use `Consulta_DNPRC` with the 14-character reference. The API returns the building listing — treat this the same as Mode 2.

A building listing holds only each unit's reference and floor/door. Surface, use, coefficient and year come only from a 20-character `Consulta_DNPRC` per unit (see Step 4).

A building with a single unit (e.g., a detached house) returns that unit's full data (`<bico>`) instead of a listing. Treat it as a building of one unit: its data is already loaded, so no further per-unit call is needed.

See [`references/catastro-api.md`](references/catastro-api.md) for full endpoint documentation, URL construction, and parameter details.

### Step 4: Parse the XML response

Extract the relevant fields from the XML response. Key fields are documented in the API reference under "XML Response Fields".

For **unit lookups** (Modes 1 and 3), extract:
- Full cadastral reference (pc1 + pc2 + car + cc1 + cc2)
- Built surface (sfc)
- Year of construction (ant)
- Participation coefficient (cpt) — it comes with a decimal comma (`4,270000` → 4.27%)
- Use classification (luso)
- Property class (cn: `UR` urban, `RU` rural) and Catastro municipality code (cmc), for the viewer link
- Postal code (dp)

For **building lookups** (Mode 2, or Mode 3 with a 14-char reference):
- Total number of units (`<control><cudnp>`)
- Building plot reference (shared pc1 + pc2)
- Per-unit reference, floor and door, from the listing
- Per-unit surface, use, coefficient and year: **one 20-character `Consulta_DNPRC` call per unit, up to 30 units**. If the building has more than 30, load the first 30, list the rest with reference, floor and door only, and ask the user whether to load the remaining units or keep the 30. Never show a per-unit value that did not come from that unit's own call. If a call fails, mark the unit as not loaded.

**Building year** is the year of construction (`ant`) returned by the unit lookups made in this answer: the unit itself in Mode 1 and Mode 3 with a 20-character reference; the loaded units in Mode 2 and Mode 3 with a 14-character reference. If the loaded units disagree, show the range (e.g., "1975–1980"). If no unit was loaded, write "Not registered". It is never taken from the listing, which has no year.

### Step 5: Enrich with building context (Mode 1 only)

When performing a unit lookup, also make a second API call with empty Planta and Puerta to get the building-level data. This provides:
- Total number of units in the building
- Building plot reference

This is a single additional HTTP call that adds valuable context.

### Step 6: Generate visualization link

Build the links described under "Catastro Visualization URL" in [`references/catastro-api.md`](references/catastro-api.md):

- **View on Catastro** (unit lookups): call `ConsultaMunicipio` with the property's province and municipality names, take the `<muni>` whose `<nm>` matches exactly, and use its `<cd>` as `del`. That call is the only source of `<cd>`, and it is often not the province code. If it fails, omit this link.
- **Units list** (`OVCListaBienes`, building lookups) and **View on map** (always): need no extra call.

### Step 7: Format the output

Structure the response following the template in [`output-template.md`](output-template.md). See [`output-example.md`](output-example.md) for a complete worked example.

## Error Handling

- If the API returns no results, inform the user and suggest possible causes: wrong street type, misspelled street name, incorrect number, floor/door not registered.
- If the API returns multiple candidate addresses, present them and ask the user to choose.
- If specific fields are empty (e.g., year of construction not registered), note "Not registered" rather than omitting the field.
- If the API is unreachable, inform the user and suggest trying again later or looking up the property directly on the Catastro website.
