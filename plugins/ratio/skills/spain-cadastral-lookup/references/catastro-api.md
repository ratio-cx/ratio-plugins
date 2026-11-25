# Catastro API Reference

Shared reference for skills that query the Spanish Catastro (Dirección General del Catastro) public web service. This API covers every province and municipality of Spain **except the foral territories** — Álava, Gipuzkoa, Navarra and Bizkaia — which keep their own cadastres and are not in the service (`ConsultaProvincia` returns 48 provinces). For an address there, tell the user the Catastro does not hold it and point them to that territory's own cadastre.

## Base URL

```
https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/
```

## Endpoints

### Consulta_DNPLOC — Lookup by address

Returns cadastral data for a property identified by its physical address.

```
GET OVCCallejero.asmx/Consulta_DNPLOC
  ?Provincia={province}
  &Municipio={municipality}
  &Sigla={street_type}
  &Calle={street_name}
  &Numero={number}
  &Bloque=
  &Escalera=
  &Planta={floor}
  &Puerta={door}
```

- When **Planta** and **Puerta** are provided: returns the full data of that unit (`<bico>`).
- When **Planta** and **Puerta** are empty: returns the building-level listing (`<lrcdnp>`), which has **only the reference and location of each unit** — see "Building-level data" below.
- A building with a single unit returns that unit's full data (`<bico>`) instead of a listing.

### Consulta_DNPRC — Lookup by cadastral reference

Returns cadastral data for a property identified by its cadastral reference number.

```
GET OVCCallejero.asmx/Consulta_DNPRC
  ?Provincia=
  &Municipio=
  &RC={cadastral_reference}
```

The first 14 characters of the reference identify the plot; characters 15-20 identify the specific unit.

- With a **20-character** reference: returns the full data of that unit (`<bico>`).
- With a **14-character** reference: returns the same building-level listing as `Consulta_DNPLOC` without floor and door — references and locations only.

### ConsultaProvincia — List provinces

```
GET OVCCallejero.asmx/ConsultaProvincia
```

Returns all Spanish provinces with their names. Use this to validate or look up province names when the user provides an ambiguous location.

### ConsultaMunicipio — List municipalities

```
GET OVCCallejero.asmx/ConsultaMunicipio
  ?Provincia={province}
  &Municipio=
```

Returns the municipalities of a province, each in a `<muni>` element:

| XML path | Field |
|----------|-------|
| `<muni><nm>` | Municipality name |
| `<muni><locat><cd>` | Catastro delegation code — needed for the viewer URL, and returned by no other endpoint |
| `<muni><locat><cmc>` | Catastro municipality code |
| `<muni><loine><cp>` / `<cm>` | INE province / municipality codes |

`Municipio` matches by **substring**: `Provincia=MADRID&Municipio=MADRID` returns Madrid, Humanes de Madrid, Las Rozas de Madrid and Rivas-Vaciamadrid. Take the `<muni>` whose `<nm>` equals the property's municipality name (`<nm>` in the property's own response), never simply the first one.

Use it to validate or look up municipality names, and to get `<cd>` for the viewer URL.

## Street Type (Sigla) Mapping

The Catastro API requires a street type code (`Sigla`). Map the user's input to the correct code:

| Sigla | Meaning | Common user input |
|-------|---------|-------------------|
| CL | Calle | calle, carrer, c/ |
| AV | Avenida | avenida, avinguda, av., avda. |
| PG | Paseo / Passeig | paseo, passeig, pg. |
| RB | Rambla | rambla, rbla. |
| CT | Carretera | carretera, ctra. |
| PL | Plaza | plaza, plaça, pl. |
| TR | Travesía / Travessera | travesía, travessera, trav. |
| PS | Pasaje / Passatge | pasaje, passatge, ptge. |
| CM | Camino / Camí | camino, camí |
| RD | Ronda | ronda |
| CR | Carrera | carrera |
| UR | Urbanización | urbanización, urb. |
| GL | Glorieta | glorieta |
| CJ | Callejón | callejón |
| BO | Barrio | barrio |
| DS | Diseminado | diseminado |

When the user provides a bare street name (e.g., "Praga 14"), default to `CL` (Calle) as it is by far the most common.

## Floor Code Conventions

Floor codes are what each building's record uses, not a fixed vocabulary: the same floor can be coded differently from one building to another. Map user input to the most likely code:

| Code | Meaning | Common user input | Status |
|------|---------|-------------------|--------|
| 0, 00 | Bajo / Baixos (ground floor) | bajo, baixos, planta baja | Verified. `BJ` is **not** accepted — it returns "no existe ningún inmueble" |
| EN | Entresuelo / Entresòl | entresuelo, entresòl, entlo. | Verified |
| PR | Principal | principal, pral. | Verified (Rambla Catalunya 50, Barcelona) |
| 01-99 | Numbered floors | 1a planta, planta 1, piso 1, 2o, 3er | Verified (`01` and `1` both work) |
| +1 | Floor above the ground floor, as some buildings code it | — | Observed; meaning not documented by the API. Send it as `%2B1`: a bare `+` in a query string is read as a space |
| AT | Ático / Àtic | ático, àtic | Not verified |
| ST | Sobreático | sobreático | Not verified |
| SS | Sótano / Subsòl | sótano, subsòl, -1, -2 | Not verified; negative floors (`-1`, `-2`) appear in construction breakdowns |

**If a unit query returns "no existe ningún inmueble"**, do not guess another code: query the building listing (Planta and Puerta empty) and pick the unit whose `<loint><pt>` (floor) and `<pu>` (door) match what the user said. Then look it up with its 20-character reference. If none matches unambiguously, show the user the floors and doors in the listing and ask.

Door identifiers are passed as-is (e.g., "1", "1a", "A", "01", "2N").

## XML Response Fields

The API returns XML. Key fields to extract:

### Unit-level data (from `<bico><bi>`)

Only a unit response carries these fields: a 20-character `Consulta_DNPRC`, a `Consulta_DNPLOC` with floor and door, or a single-unit building.

| XML path | Field | Description |
|----------|-------|-------------|
| `<bi><idbi><rc><pc1>` + `<pc2>` + `<car>` + `<cc1>` + `<cc2>` | Cadastral reference | Full 20-character reference |
| `<bi><idbi><rc><pc1>` + `<pc2>` | Plot reference | 14-character plot identifier |
| `<bi><idbi><cn>` | Property class | `UR` urban, `RU` rural |
| `<bi><debi><sfc>` | Built surface (m2) | Official registered built surface |
| `<bi><debi><ant>` | Year of construction | Year the building was constructed |
| `<bi><debi><cpt>` | Participation coefficient | Unit's share of the building, as a percentage with a **decimal comma** (e.g., `4,270000` = 4.27%). Replace the comma with a point before using it as a number |
| `<bi><debi><luso>` | Use | Classification: Residencial, Comercial, etc. |
| `<bi><dt><loine><cp>` | Province code (INE) | Two-digit INE province code |
| `<bi><dt><loine><cm>` | Municipality code (INE) | INE municipality code (Barcelona: 19) |
| `<bi><dt><cmc>` | Municipality code (Catastro) | Catastro municipality code (Barcelona: 900). Differs from the INE code in thousands of municipalities |
| `<bi><dt><np>` / `<nm>` | Province / municipality name | |
| `<bi><dt><locs><lous><lourb><dir><cv>` | Street code | Catastro internal street code |
| `<bi><dt><locs><lous><lourb><dir><pnp>` | Street number | Building street number |
| `<bi><dt><locs><lous><lourb><loint><es>` / `<pt>` / `<pu>` | Staircase / floor / door | As coded in the record (see Floor Code Conventions) |
| `<bi><dt><locs><lous><lourb><dp>` | Postal code | e.g., `08025` |
| `<bi><dt><locs><lous><lourb><dm>` | District | e.g., `6`. Not a municipality code |

### Building-level data (from `<lrcdnp>`)

A building listing contains one `<rcdnp>` per unit with **only** its reference (`<rc>`) and location (`<dt>`: codes, street, `<loint>` staircase/floor/door, postal code). A listing is what `Consulta_DNPLOC` returns without floor and door, and what `Consulta_DNPRC` returns for a 14-character reference. There are no `<bice>` elements and **no surface, use, coefficient or year per unit**. Extract:

- **Total unit count**: `<control><cudnp>`, which equals the number of `<rcdnp>` elements
- **Building prefix**: the shared first 14 characters of the cadastral reference (pc1 + pc2)
- **All units**: reference, floor and door of each

**Per-unit characteristics need one 20-character `Consulta_DNPRC` call per unit.** For the Unit Directory:

1. Call `Consulta_DNPRC` for each unit, in listing order, **up to 30 units**.
2. If the building has **more than 30 units**, stop at 30. List the remaining units with reference, floor and door only, and ask the user whether to load the rest or keep the first 30.
3. Never fill a unit's surface, use, coefficient or year from anything but that unit's own 20-character response. If a call fails, mark that unit's values as not loaded and say so. Never estimate them or copy them from another unit.

## Catastro Visualization URL

Link to the property's page on the Sede Electrónica del Catastro:

```
https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCConCiud.aspx?del={cd}&mun={cmc}&UrbRus={U|R}&RefC={full_cadastral_reference}
```

| Parameter | Value | Where it comes from |
|-----------|-------|---------------------|
| `del` | Catastro delegation code `<cd>` | **Only** `ConsultaMunicipio` (`<muni><locat><cd>`), so make that call for every link. It usually equals the INE province code `<cp>`, but not always (Gijón: `cd=52`, `cp=33`), and a wrong `del` sends the page to an error |
| `mun` | Catastro municipality code `<cmc>` | The property's own response (`<dt><cmc>`), or `ConsultaMunicipio`. **Not** the INE code `<cm>` |
| `UrbRus` | `U` for urban, `R` for rural | `<idbi><cn>`: `UR` → `U`, `RU` → `R` |
| `RefC` | The 20-character reference | |

Example (Barcelona: `cd=8`, `cmc=900`):
`https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCConCiud.aspx?del=8&mun=900&UrbRus=U&RefC=0143706DF3804C0014PW`

`RefC` alone, or INE codes in `del`/`mun`, sends the page to `OVCErrorDatos.aspx`. If `ConsultaMunicipio` fails, leave this link out and keep the two below, which need no codes.

The plot's unit list, and the natural link for a building lookup:

```
https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCListaBienes.aspx?rc1={pc1}&rc2={pc2}
```

The map viewer:

```
https://www1.sedecatastro.gob.es/Cartografia/mapa.aspx?refcat={14_char_plot_reference}
```

## Error Handling

- **No results found**: the response contains `<err><cod>` with an error code and `<des>` with a description. Common: street not found, number not found, floor/door not found. For floor/door not found, see the fallback in Floor Code Conventions.
- **Multiple matches**: the API may return a list of candidate addresses when the street name is ambiguous. Present options to the user.
- **Network/timeout errors**: tell the user the Catastro service is unreachable and suggest retrying later or looking up the property directly on the Sede Electrónica del Catastro. Never substitute data from other sources: the value of a lookup is that the data is official.
- **Empty fields**: some fields (especially `cpt`, `ant`) may be empty for very old properties or special cases. Note this in the output rather than failing.

## Usage Notes

- Province and municipality names are passed as the user specifies them — the API accepts full names in uppercase (e.g., "BARCELONA", "MADRID", "SEVILLA"). The API is case-insensitive but conventionally uses uppercase.
- Street names should be passed without the street type prefix (e.g., "PRAGA" not "CALLE PRAGA").
- The API is free, public, and does not require authentication.
- Response format is XML; parse it by extracting the relevant fields documented above.
