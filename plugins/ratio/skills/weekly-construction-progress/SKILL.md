---
name: weekly-construction-progress
description: Weekly construction progress photo report as a PowerPoint slide, from site photos. Use for "seguimiento de obra", "reportaje fotográfico" or "fotos de obra de la semana".
metadata:
  version: "1.0.0"
---

# Weekly Construction Progress Report

Build the weekly progress slide of a construction site: one photo per viewpoint (1 to 8 vertical 9:16 photos), the date and time each was taken, and a few observations. Week after week, the same viewpoints, so anyone can see how the works advance.

The bundled engine does every deterministic step: reading the photos' metadata, computing weeks, drawing contact sheets, writing the PowerPoint and keeping the history. You choose which photo goes to each viewpoint, write the observations, and agree the photos with the user.

**Invent nothing.** Dates and weeks come from the photos; observations describe only what the chosen photos show.

## Language

Reply in the language the user writes in, unless they ask for another.
This covers everything the user sees: answers, table headers, reports.
Use the terms and formatting rules in [`references/glossary.md`](references/glossary.md).

## The two folders

The skill works only with two of the user's local folders, connected to Cowork. Where they come from does not matter (a plain folder, or one synced with a cloud service).

| Folder | What for | Access |
|---|---|---|
| **Photo folder** | The site photos, in any structure of subfolders | **Read only: never write, move or delete anything in it** |
| **Working folder** | The reports, and the skill's own folder `_claude-skill-config/` | Read and write |

A connected folder is at `$HOME/mnt/<folder name>`. Inside the working folder:

```
<working folder>/
├── 2026-S41 Seguimiento de obra - P-007 Calle Mayor 12.pptx
└── _claude-skill-config/          WORK below
    ├── config.json                project, photo folder name, zones, template
    ├── reports.json               history: the photo chosen for each zone, week by week
    ├── template.pptx              only when the user customised or brought a template
    └── cache/                     regenerable: metadata, specs, contact sheets, previews
```

Formats of every file, and the template markers, are in [`formats.md`](formats.md). A folder set up by the earlier Spanish version of this skill (`catalogo.json`, Spanish keys) is migrated by the engine the first time it reads it; nothing to do.

## The engine

`scripts/site_progress.py`, inside this skill's directory. Python 3.10+, with Pillow and python-pptx. Run it as `python3 <skill dir>/scripts/site_progress.py <command>`; below, `sp` stands for that. Every command prints JSON; on failure, `"ok": false` with a stable `error` code, a `message`, and exit 2. If `error` is `missing_dependency`, run the `install` command it gives and retry. Run commands one at a time, with a generous timeout for `scan` and `overview` (hundreds of photos take a while).

| Command | What it does |
|---|---|
| `check PHOTOS` | Are the files readable? `unreadable > 0` means a synced folder keeps them in the cloud only |
| `scan PHOTOS WORK` | Reads every photo's metadata into the cache (incremental): duplicates, photos without a date |
| `weeks WORK` | ISO weeks with photos, the `latest`, and `reports_done` |
| `overview WORK` | Contact sheets of every photo, numbered in time order, to define the zones |
| `refsheet WORK --week W` | Each zone's reference photo (from the last report before W, else from the config) and a sheet |
| `candidates WORK --week W` | That week's photos with hints (`ultra_wide`, `vertical`, `heading`, `near_heading`) and sheets |
| `choices WORK --spec S --alts A` | Choice sheet: per zone, the chosen photo (✓, green) and alternatives A, B, C |
| `build WORK --spec S --out F` | Writes the slide, records it in the history, returns a `preview` image |
| `template new WORK [--accent --card --font --logo --brand]` | The neutral template, customised, saved as the project's template |
| `template use WORK DECK` | Adopts the user's own deck, once it carries the markers |
| `template check DECK` | Which markers a deck has and which it lacks |

`W` is the ISO week written `2026-W41`, even though report file names say `2026-S41`, and the user may say "semana 41".

Contact sheets and previews are JPEG files under `WORK/cache/sheets/`. Open them to look at them, and show them to the user when they need to see them too.

## Workflow

### 1. Find or create the setup

Look for `$HOME/mnt/*/_claude-skill-config/config.json` and `$HOME/mnt/*/*/_claude-skill-config/config.json`.

**Found** (several: ask which project). The working folder is the one holding `_claude-skill-config/`; the photo folder is the connected folder named in `photos`. If it is not connected, ask the user to connect it. Go to step 2.

**Not found** (first run). Ask only for the two folders, offering the connected ones as options: the **working folder** and the **photo folder**. Ask the user to connect any that is missing. Then:

1. The working folder must not be the photo folder or lie inside it: the photo folder is read only, and `scan` refuses it (`work_inside_photos`). If the user picks one, ask for another. Then check you can write: `mkdir -p "<working folder>/_claude-skill-config/cache"`. If it fails, ask for another folder.
2. Ask for the project's code and name (e.g. `P-007 · Calle Mayor 12`).
3. Run step 2 (`check`, `scan`).
4. **Zones.** `sp overview WORK`, then look at every sheet. Propose 4 to 8 zones that **recur across the weeks**, the recent ones above all, favouring general views. For each: a name, a description, the weeks it appears in, and 3 to 5 reference photos. Show a table and adjust until the user agrees.
5. Write `config.json` with Python: project, photo folder name and zones (format in [`formats.md`](formats.md)). Show a summary.
6. **Template.** Offer three choices:
   - **The neutral template** as it is: nothing to do.
   - **The neutral template, customised**: an accent colour, the font, and the user's logo (an image in a connected folder) or a brand name as text. `sp template new WORK --accent "#0A6E5A" --font "Helvetica" --logo "<path>"`.
   - **Their own PowerPoint**: they type the markers into their deck's first slide (see [`formats.md`](formats.md#template-markers)), then `sp template use WORK "<deck>"`. If it fails with `template_missing_markers`, tell them which markers are missing and where they go, and retry when they have added them.

   Both commands add the `template` key to `config.json` and keep the rest of the file.
7. Go on with step 3 to build the first report, and show its preview before calling the setup done.

The zones and the template can change at any time: run `template new` / `template use` again, or edit `config.json`. **When you edit `config.json`, load it, change only what you need and save it back: never rewrite it from scratch, or the `template` key is lost.**

### 2. Photos and metadata

`PHOTOS` and `WORK` are the folders' paths under `$HOME/mnt`.

1. `sp check PHOTOS`. If `unreadable > 0`, the files exist but cannot be read: the synced folder keeps them in the cloud only. Ask the user to make the folder **available offline** in their sync service, and check again every minute or so.
2. `sp scan PHOTOS WORK`. If it gives a `hint` about HEIC photos, run the install command in it and scan again. Mention photos without a date: they cannot be placed in any week. Photos in `dated_from_file_name` (WhatsApp above all) carry the date the file was received or saved, not always the one it was taken: if any of them is a candidate, tell the user and ask them to confirm its week.

### 3. The week

The week is the **ISO week of the capture date**: the EXIF date, or a date in the file name (WhatsApp, Android). Never the folder name or the file's modification date.

`sp weeks WORK`:
- If the user named no week, propose the `latest`, and warn if it is the current week (a site visit may still be missing).
- If that week is in `reports_done`, ask whether to rebuild it.
- If the week has no photos, say so and offer the nearest weeks.

### 4. One photo per zone

1. `sp refsheet WORK --week W`: the reference photo of each zone.
2. `sp candidates WORK --week W`: the candidates and their sheets. Look at every sheet.
3. For each zone, choose a **main photo** and up to **3 alternatives**, best first:
   - Prefer general views (often `ultra_wide`) over details, and vertical photos over horizontal ones, which get cropped.
   - Compare with the reference by eye. `near_heading` is only a hint: GPS cannot tell zones apart, and altitude is unreliable.
   - If nothing fits, leave the zone **without a photo**. Never reuse an earlier week's photo. Offer the doubtful candidates as alternatives.
   - If a relevant new space shows up, suggest adding or replacing a zone.
4. Save `WORK/cache/spec_<W>.json` and `WORK/cache/alts_<W>.json` ([`formats.md`](formats.md)).

### 5. Observations and the first version

1. Write 2 to 5 observations, `Zone: observable fact.`, only from what the chosen photos show, and mention the zones without a photo. **Do not ask the user for them**: they go straight into the slide.
2. Fill the spec's `labels` in the reply's language (example in [`formats.md`](formats.md)), with the glossary's terms and date format. They cover the slide and the choice sheet.
3. `sp build WORK --spec WORK/cache/spec_<W>.json [--replace] --out "<working folder>/<file name>"`. The file name follows the user's language and the history's pattern: `2026-S41 Seguimiento de obra - P-007 Calle Mayor 12.pptx` in Spanish, `2026-W41 Construction progress - P-007 Calle Mayor 12.pptx` in English. Leave out characters a file name cannot hold (`/`, `:`, `·`).
   - `photo_outside_week`: a chosen photo was not taken in that week, or has no date. Choose another one, or leave the zone without a photo.
   - `output_exists`: a file with that name exists and the history does not know it (the user may have edited it). Ask the user before running the build again with `--replace`, or use another name.
4. `sp choices WORK --spec ... --alts ...`: the choice sheet.
5. Look at `preview` (a drawing of the slide, close to PowerPoint's) and check the layout. Show the user **the preview and the choice sheet**.

`zones_not_in_config` in the result lists zones the spec has and `config.json` lacks: add them, or fix the name.

### 6. The user's choice

1. Ask only about the zones that have alternatives (at most 4 questions at a time). Options per zone: keep ✓, A, B, C; free text for "no photo" or another photo.
2. If a photo changes: update the spec, **rewrite the observations for those zones** after looking at the new photos, run `build` again with the same `--out` (it replaces the file and the history entry), and show the new preview. Repeat until the user approves the photos.

### 7. Delivery

1. The report's path in the working folder, in a code block.
2. A summary: the week, the zones with and without a photo, and that the report is in the history. Remind the user that you wrote the observations and they can edit them in the PowerPoint.

## Rules

- Never modify, move or delete anything in the photo folder.
- Never store absolute paths in `config.json` or `reports.json`: photo paths are relative to the photo folder, the photo folder is stored by name.
- Old sheets pile up in `cache/sheets/`; that is expected, and the cache can be deleted at any time.
- If something fails, explain why in plain words and propose the next step.

## Limits

- One slide per week, 1 to 8 viewpoints, vertical 9:16 photos (horizontal ones are cropped).
- Photos only: videos are skipped.
- One project per working folder.
- HEIC photos need the `pillow-heif` package; the engine says when.
- The preview is an approximation drawn by the engine; fonts and exact spacing may differ slightly in PowerPoint.
