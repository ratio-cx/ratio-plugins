# Formats

The files the engine reads and writes inside `WORK` (`<working folder>/_claude-skill-config/`). Paths to photos are always relative to the photo folder, with `/` as separator.

## config.json

```json
{
 "version": 3,
 "project": "P-007 · Calle Mayor 12",
 "photos": "6_Registro Fotografico",
 "zones": [
  {"name": "Fachada principal", "description": "General view from the street",
   "references": ["07_Septiembre/IMG_2236.JPG", "08_Octubre/IMG_2909.JPG"]}
 ]
}
```

- `photos`: the photo folder's **name**, not its path, to find it among the connected folders in every session.
- `template`: absent in a new setup, which means the neutral template. `template new` and `template use` add it (`"template": "template.pptx"`); never write it by hand.
- `zones`: the viewpoints, in the slide's order. `references` run from oldest to newest; they are used while a zone has no photo in any report yet.

## Spec: `cache/spec_<week>.json`

```json
{
 "project": "P-007 · Calle Mayor 12",
 "week": "2026-W41",
 "labels": {
  "title": "SEGUIMIENTO DE OBRA / REPORTAJE FOTOGRÁFICO",
  "week": "SEMANA {week} · {year}",
  "summary": "{n} PUNTOS DE VISTA · REPORTE SEMANAL",
  "observations": "OBSERVACIONES DE LA SEMANA",
  "no_photo": "SIN FOTO ESTA SEMANA",
  "date_format": "%d/%m/%Y",
  "time_format": "%H:%M",
  "choices_title": "{week} · elegida (verde) y alternativas",
  "no_photo_short": "sin foto",
  "cropped": "H: se recorta",
  "cannot_open": "no se puede abrir",
  "no_alternatives": "Sin foto ni alternativas:"
 },
 "slots": [
  {"zone": "Fachada principal", "path": "08_Octubre/IMG_3011.JPG"},
  {"zone": "Portal", "path": null}
 ],
 "observations": ["Fachada principal: andamio montado en toda la altura.", "Portal: sin foto esta semana."]
}
```

- `slots`: one per zone, in `config.json`'s order. `path: null` is a zone without a photo.
- `labels`: every text the slide shows besides the project, zones and observations. `{week}` is the two-digit week, `{year}` the ISO year, `{n}` the two-digit number of viewpoints. The last five keys are the choice sheet's; in `choices_title`, `{week}` is the whole ISO week (`2026-W41`). `date_format` and `time_format` are Python `strftime` formats: `%d/%m/%Y` for Spanish and Catalan, `%d %b %Y` for English (the glossary's formats). Missing labels fall back to English.
- `date` (optional): the date in the header. By default, the latest capture among the chosen photos.

## Alternatives: `cache/alts_<week>.json`

```json
{"Fachada principal": ["08_Octubre/IMG_3012.JPG", "08_Octubre/IMG_3020.JPG"]}
```

Up to 3 per zone, best first; the choice sheet labels them A, B, C.

## reports.json

Written only by `build`; never edit it by hand.

```json
{"reports": [
 {"week": "2026-W41", "date": "08/10/2026", "generated": "2026-10-09T12:00:00",
  "file": "2026-S41 Seguimiento de obra - P-007 Calle Mayor 12.pptx",
  "observations": ["..."],
  "slots": [{"zone": "Fachada principal", "path": "08_Octubre/IMG_3011.JPG", "md5": "...", "heading": 12}]}
]}
```

## Template markers

A template is a PowerPoint (`.pptx`) whose **first slide** carries these markers, typed as text inside its shapes. The build replaces each one and keeps the formatting of the text it replaces. Other slides are dropped; everything else on the first slide (logos, lines, colours) stays as it is.

| Marker | Required | Becomes |
|---|---|---|
| `{{project}}` | yes | The project's code and name. Text around it stays: `Obra: {{project}}` |
| `{{week}}` | yes | The `week` label, e.g. `SEMANA 41 · 2026` |
| `{{photos}}` | yes | Type it inside a **rectangle**: the rectangle marks the area for the photos and the observations. Each viewpoint card and the observations box copy its fill and border, and the labels copy the marker's font, size and colour |
| `{{date}}` | no | The report's date |
| `{{title}}` | no | The `title` label |
| `{{summary}}` | no | The `summary` label, e.g. `06 PUNTOS DE VISTA · REPORTE SEMANAL` |

How to tell the user to add them: open the deck in PowerPoint, type `{{project}}` and `{{week}}` where those texts should go, and draw a rectangle over the area for the photos with the text `{{photos}}` inside. `template check` lists what is still missing.
