# Cadastral Data Report

## Property Identification

| Field | Value |
|-------|-------|
| Cadastral reference | {full 20-character reference} |
| Official address | {Sigla} {street name} {number}, {floor} {door} |
| Province | {province name} |
| Municipality | {municipality name} |

## Property Characteristics

> Unit lookups only (Mode 1, and Mode 3 with a 20-character reference). Omit this section in a building lookup: a building has no surface, use or coefficient of its own, and one unit's values must never be shown as the building's. A building with a single unit is the exception: show that unit's data here.

| Field | Value |
|-------|-------|
| Built surface | {X} m2 |
| Useful surface (approx.) | {X * 0.80} m2 |
| Year of construction | {year} |
| Use | {Residencial / Comercial / etc.} |
| Participation coefficient | {X}% |
| Postal code | {postal code if available} |

> **Note on surfaces:** Built surface includes the proportional share of common areas (stairways, hallways, etc.). Useful (livable) surface is typically around 80% of the built surface, though this varies by building layout.

## Construction Breakdown

> Include this section only if the API returns detailed construction breakdown data (multiple `<scons>` entries with different use types or reform years). Omit if only one entry matches the main property data.

| Use | Surface (m2) | Reform year |
|-----|-------------|-------------|
| {use type} | {surface} | {year or "—"} |
| **Total** | **{total}** | |

## Building Context

| Field | Value |
|-------|-------|
| Building plot reference | {first 14 characters of cadastral ref} |
| Total units in building | {count} |
| Building year | {year from the unit lookups made; range if they differ} |

## Unit Directory

> Include this section in building lookup mode (Mode 2) and when a building-level cadastral reference is provided (Mode 3 with 14-char reference). Floor, door and reference come from the building listing. Surface, use and coefficient come **only** from each unit's own 20-character lookup, made for up to 30 units. A unit whose lookup was not made, or failed, shows "—" in those three columns. Never fill them with an estimate or with another unit's values.

| Floor | Door | Surface (m2) | Use | Coef. (%) | Cadastral Reference |
|-------|------|-------------|-----|-----------|---------------------|
| {floor} | {door} | {surface} | {use} | {cpt} | {full reference} |
| ... | ... | ... | ... | ... | ... |

**Total units:** {count}

> Only when the building has more than 30 units: "Details requested for the first 30 of {count} units ({loaded} loaded); the other {count − 30} are listed with floor, door and reference only. Do you want me to load the rest ({count − 30} more lookups), or keep it at 30?"
>
> Only when a lookup failed: "{n} units could not be loaded ("—")." Give a cause only if the response stated one (e.g., the Catastro service was unreachable).

## Links

- [View on Catastro]({visualization_url}) — official Catastro property page (unit lookups; omit if the delegation code could not be obtained)
- [Units list]({units_list_url}) — every unit of the plot on the Catastro (building lookups)
- [View on map]({map_url}) — Catastro cartography viewer

---

> **Note:** Data sourced from the Dirección General del Catastro public service. Cadastral data is official but may not reflect recent modifications pending registration. For legal purposes, always verify with a current nota simple from the Registro de la Propiedad.
