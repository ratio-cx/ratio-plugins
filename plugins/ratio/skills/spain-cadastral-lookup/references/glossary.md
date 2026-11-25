# Glossary

Canonical terms for user-facing output. Skill instructions are written in English; the user sees the column that matches the language of the reply.

A term belongs here only if it appears in user-facing output **and** its translation is not obvious or it carries a specific legal or official meaning. General vocabulary does not. Catastro API codes (`CL`, `BJ`, `sfc`...) live in `catastro-api.md`, which maps user input to codes; this file maps concepts to the labels the user reads.

## Rules

Every term carries one rule:

| Rule | How to render the term |
|---|---|
| `translate` | Use the term from the column of the reply's language |
| `translate-gloss` | As `translate`. In any language other than Spanish or Catalan, add the Spanish term in parentheses on first mention: "cadastral reference (referencia catastral)" |
| `keep-es` | Spanish and Catalan replies use their own column. Any other language keeps the Spanish term and explains it once, using the EN column as the gloss: "nota simple (land registry extract)". The EN column is a gloss, never a standalone translation |
| `keep-acronym` | Keep the acronym in every language and spell it out on first mention |

Languages without a column (e.g. French) follow the same rules: translate `translate` terms naturally, and treat every other rule as a language other than Spanish or Catalan.

## Formatting

| Locale | Numbers | Currency | Dates | Area |
|---|---|---|---|---|
| en | 1,234.56 | €1,234.56 | 23 Sep 2026 | m² |
| es, ca | 1.234,56 | 1.234,56 € | 23/09/2026 | m² |

## Cadastre and registry

| EN | ES | CA | Definition | Rule |
|---|---|---|---|---|
| Cadastre | Catastro | Cadastre | State registry of real estate for tax purposes | translate |
| Directorate General for the Cadastre | Dirección General del Catastro | Direcció General del Cadastre | Public body that runs the Catastro | keep-es |
| cadastral reference | referencia catastral | referència cadastral | 20-character unit identifier; the first 14 characters identify the plot | translate-gloss |
| RC | RC | RC | Abbreviation of referencia catastral | keep-acronym |
| plot reference | referencia de parcela | referència de parcel·la | First 14 characters of the cadastral reference | translate |
| Land Registry | Registro de la Propiedad | Registre de la Propietat | Legal registry of ownership and charges; distinct from the Catastro | keep-es |
| land registry extract | nota simple | nota simple | Informative extract of a property's entry in the Land Registry | keep-es |
| horizontal division | división horizontal | divisió horitzontal | Legal split of a building into independent units | translate |

## Property characteristics

| EN | ES | CA | Definition | Rule |
|---|---|---|---|---|
| built surface | superficie construida | superfície construïda | Surface including the unit's share of common areas | translate |
| useful surface | superficie útil | superfície útil | Livable interior area, excluding walls and common areas | translate |
| participation coefficient | coeficiente de participación | coeficient de participació | The unit's share of the building, as a percentage | translate |
| year of construction | año de construcción | any de construcció | Year the building was constructed, as registered | translate |
| use | uso | ús | Cadastral use class (residential, commercial...) | translate |
| unit | inmueble | immoble | A single registered property within a building | translate |
| building | edificio / finca | edifici / finca | "Finca" is the usual word in Catalonia | translate |

## Floor labels

| EN | ES | CA | Definition | Rule |
|---|---|---|---|---|
| basement | sótano | soterrani | Any floor below street level | translate |
| ground floor | bajo | planta baixa / baixos | Street-level floor | translate |
| mezzanine floor | entresuelo | entresòl | Intermediate floor between the ground floor and the principal | keep-es |
| principal floor | principal | principal | First full floor above the entresuelo, traditionally the main one | keep-es |
| top floor | ático | àtic | Top floor, usually set back with a terrace | translate |
| upper top floor | sobreático | sobreàtic | Floor above the ático | translate |

## VAT

Catalan terms in this section are drafts pending domain review.

| EN | ES | CA | Definition | Rule |
|---|---|---|---|---|
| VAT regularization | regularización de IVA | regularització de l'IVA | Adjustment of VAT deducted on an investment good when its use changes within the regularization period | translate-gloss |
| investment good | bien de inversión | bé d'inversió | Good used for more than one year as an instrument of work (art. 108 LIVA); buildings held for sale are inventory, not investment goods | translate-gloss |
| inventory | existencias | existències | Goods held for sale in the ordinary course of business | translate |
| regularization period | periodo de regularización | període de regularització | For buildings, the year use starts plus the nine following calendar years | translate |
| input VAT borne | IVA soportado | IVA suportat | VAT charged to the buyer, or self-assessed under the reverse charge, before any deduction | translate-gloss |
| deduction percentage | prorrata | prorrata | Share of input VAT the business may deduct; 100% if all its operations give a right to deduct | translate-gloss |
| waiver of the exemption | renuncia a la exención | renúncia a l'exempció | Option to tax an otherwise exempt second supply of a building with VAT (art. 20.Dos LIVA) | translate-gloss |
| reverse charge | inversión del sujeto pasivo | inversió del subjecte passiu | The buyer, not the seller, self-assesses the VAT (art. 84.Uno.2.e LIVA) | translate-gloss |
| exempt supply | entrega exenta | lliurament exempt | Sale not taxed under VAT; for buildings it is taxed under ITP instead | translate-gloss |
| subject and not exempt supply | entrega sujeta y no exenta | lliurament subjecte i no exempt | Sale taxed under VAT | translate-gloss |
| self-supply | autoconsumo | autoconsum | Change of use of a good within the business treated as a supply for VAT (art. 9.1º LIVA) | translate-gloss |
| first supply | primera entrega | primer lliurament | First sale of a new or refurbished building by its developer (art. 20.Uno.22º LIVA) | translate-gloss |
| second supply | segunda entrega | segon lliurament | Any later sale of a building; exempt from VAT unless the exemption is waived | translate-gloss |
| VAT | IVA | IVA | Value added tax (Impuesto sobre el Valor Añadido) | translate |
| ITP | ITP | ITP | Impuesto sobre Transmisiones Patrimoniales, the transfer tax on exempt sales | keep-acronym |
| AJD | AJD | AJD | Actos Jurídicos Documentados, the stamp duty on deeds | keep-acronym |
| LIVA | LIVA | LIVA | Ley 37/1992 del Impuesto sobre el Valor Añadido, the Spanish VAT act | keep-acronym |

## Auctions

| EN | ES | CA | Definition | Rule |
|---|---|---|---|---|
| charges | cargas | càrregues | Prior debts secured on the property (mortgages, liens) that the buyer at auction takes on | translate-gloss |
| auction valuation | valoración | valoració | The AEAT's appraisal of the property for the auction; not a market price | translate-gloss |
| full ownership | pleno dominio | ple domini | Ownership with the right to use, rent and sell the property | translate-gloss |
| bare ownership | nuda propiedad | nua propietat | Ownership without the use, which belongs to the usufructuary until the usufruct ends | translate-gloss |
| usufruct | usufructo | usdefruit | The right to use a property and collect its rent without owning it | translate-gloss |
| usufructuary | usufructuario | usufructuari | Holder of a usufruct | translate |
| ownership share | porcentaje de titularidad | percentatge de titularitat | Part of the right that is auctioned, e.g. 25 % of a flat | translate |
| timeshare | multipropiedad (aprovechamiento por turnos) | multipropietat (aprofitament per torns) | The use of a property for some weeks a year, not the property itself | translate-gloss |
| surface right | derecho de superficie | dret de superfície | Ownership of a building on someone else's land for a fixed term | translate-gloss |
| inheritance rights | derechos hereditarios | drets hereditaris | An heir's share in an inheritance that has not been divided yet | translate-gloss |
| net | neto | net | Auction valuation minus charges | translate |
| deposit | depósito | dipòsit | Amount a bidder pays in advance to take part in the auction | translate |
| AEAT | AEAT | AEAT | Agencia Estatal de Administración Tributaria, the Spanish Tax Agency (Hacienda) | keep-acronym |
| BOE | BOE | BOE | Boletín Oficial del Estado; its auction portal is where bids are placed | keep-acronym |

## Construction progress

| EN | ES | CA | Definition | Rule |
|---|---|---|---|---|
| construction progress report | seguimiento de obra | seguiment d'obra | Periodic record of how the works on a site advance, usually weekly | translate |
| photo report | reportaje fotográfico | reportatge fotogràfic | A report made of site photos, one per viewpoint | translate |
| viewpoint | punto de vista | punt de vista | A spot on the site photographed from the same place every week, so progress can be compared | translate |
