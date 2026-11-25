#!/usr/bin/env python3
"""Engine of the weekly-construction-progress skill.

Commands (every one prints JSON on stdout; on failure `"ok": false`, a stable
`error` code and exit status 2):

  check      PHOTOS                        are the files readable (not cloud-only)?
  scan       PHOTOS WORK                   read every photo's metadata -> WORK/cache/meta.json
  weeks      WORK                          ISO weeks that have photos, and the reports done
  candidates WORK --week 2026-W41          that week's photos, with hints, and contact sheets
  overview   WORK                          contact sheets of every photo (to define the zones)
  refsheet   WORK [--week 2026-W41]        each zone's reference photo, and a sheet
  choices    WORK --spec S --alts A        choice sheet: chosen photo and alternatives per zone
  build      WORK --spec S --out F.pptx    write the slide and record it in the history
  template new   WORK [--accent --font --logo --brand]   customised neutral template
  template use   WORK DECK.pptx            adopt the client's own deck as the template
  template check DECK.pptx                 does a deck carry the markers the build needs?
  version

WORK is the skill's own folder inside the user's working folder
(<working folder>/_claude-skill-config). It holds:
  config.json    project, name of the photo folder, zones, template
  reports.json   history: the photo chosen for each zone, week by week
  template.pptx  the template in use, when one was configured
  cache/         meta.json, overview.json, specs, contact sheets (all regenerable)

The photo folder is only ever read. Python 3.10+. Needs Pillow and python-pptx;
pillow-heif, when installed, adds HEIC photos.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys

VERSION = "1.0.0"
META_VERSION = 3
CONFIG_VERSION = 3
STAMP = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # sheets never reuse a file name

IMG_EXT = {".jpg", ".jpeg", ".png"}
HEIC_EXT = {".heic", ".heif"}
VID_EXT = {".mp4", ".mov", ".m4v", ".avi", ".3gp"}
UW_LENS = ("2.22mm", "1.54mm", "1.55mm", "ultra wide")  # iPhone ultra-wide lens names
UW_FOCAL_35 = 18  # 35 mm-equivalent focal length below which a lens is ultra-wide
HEADING_TOLERANCE = 35
INSTALL = "python3 -m pip install --user pillow python-pptx pillow-heif"

try:  # HEIC (iPhone) photos need a plugin Pillow does not ship
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
except Exception:  # noqa: BLE001 - absent or broken: HEIC files are reported, not read
    HEIC_SUPPORT = False

DEFAULT_LABELS = {
    "title": "CONSTRUCTION PROGRESS / PHOTO REPORT",
    "week": "WEEK {week} · {year}",
    "summary": "{n} VIEWPOINTS · WEEKLY REPORT",
    "observations": "OBSERVATIONS THIS WEEK",
    "no_photo": "NO PHOTO THIS WEEK",
    "date_format": "%d %b %Y",
    "time_format": "%H:%M",
    # the choice sheet, which the user sees too
    "choices_title": "{week} · chosen (green) and alternatives",
    "no_photo_short": "no photo",
    "cropped": "H: cropped",
    "cannot_open": "cannot open",
    "no_alternatives": "No photo and no alternatives:",
}
REQUIRED_MARKERS = ["{{project}}", "{{week}}", "{{photos}}"]
OPTIONAL_MARKERS = ["{{title}}", "{{date}}", "{{summary}}"]


class Fail(Exception):
    def __init__(self, code, message, **extra):
        super().__init__(message)
        self.code, self.message, self.extra = code, message, extra


def out(obj):
    print(json.dumps({"ok": True, **obj}, ensure_ascii=False, indent=1, default=str))


def load(p, default=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise Fail("bad_json", f"{p} is not valid JSON: {e}") from e


def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)


def folder(p):
    if not os.path.isdir(p):
        raise Fail("folder_not_found", f"No folder at {p}")
    return p


def readable(p):
    try:
        with open(p, "rb") as f:
            f.read(2)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- config and history


def load_config(work):
    """config.json, migrated in place from the original Spanish keys when needed."""
    p = os.path.join(work, "config.json")
    cfg = load(p, {}) or {}
    if "zonas" in cfg or "proyecto" in cfg or "fotos" in cfg:
        cfg = {"version": CONFIG_VERSION, "project": cfg.get("proyecto"), "photos": cfg.get("fotos"),
               "template": cfg.get("template"),
               "zones": [{"name": z["nombre"], "description": z.get("descripcion", ""),
                          "references": z.get("referencias", [])} for z in cfg.get("zonas", [])]}
        save(p, cfg)
    return cfg


def load_reports(work):
    """reports.json, created from the original catalogo.json when only that one exists."""
    p = os.path.join(work, "reports.json")
    rep = load(p)
    if rep is None:
        old = load(os.path.join(work, "catalogo.json"))
        rep = {"reports": []}
        if old:
            rep["reports"] = [{"week": i["semana"], "date": i.get("fecha"), "generated": i.get("generado"),
                               "file": i.get("fichero"), "observations": i.get("observaciones", []),
                               "slots": [{"zone": s["zona"], "path": s.get("path"), "md5": s.get("md5"),
                                          "heading": s.get("hdg")} for s in i.get("slots", [])]}
                              for i in old.get("informes", [])]
            save(p, rep)
    return rep


def week_arg(w):
    if w is not None and not re.fullmatch(r"\d{4}-W\d{2}", w):
        raise Fail("bad_week", f"Week must look like 2026-W41, not {w!r}")
    return w


# ---------------------------------------------------------------- check


def cmd_check(a):
    total, bad = 0, []
    for dp, _, fs in os.walk(folder(a.photos)):
        for fn in sorted(fs):
            if fn.startswith("."):
                continue
            total += 1
            p = os.path.join(dp, fn)
            if not readable(p):
                bad.append(os.path.relpath(p, a.photos))
    print(json.dumps({"ok": total > 0 and not bad, "total": total, "unreadable": len(bad),
                      "examples": bad[:5]}, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- scan


def exif_of(p):
    from PIL import ExifTags, Image

    im = Image.open(p)
    ex = im.getexif()
    sub = ex.get_ifd(0x8769)
    g = {ExifTags.GPSTAGS.get(k, k): v for k, v in ex.get_ifd(0x8825).items()}
    w, h = im.size
    if ex.get(274) in (5, 6, 7, 8):  # rotated 90°: the stored width is the visible height
        w, h = h, w
    r = {"w": w, "h": h, "make": ex.get(271), "model": ex.get(272), "dto": sub.get(36867),
         "lens": sub.get(42036), "focal35": sub.get(41989)}
    try:
        if "GPSLatitude" in g:
            r["lat"] = _dms(g["GPSLatitude"], g.get("GPSLatitudeRef", "N"))
            r["lon"] = _dms(g["GPSLongitude"], g.get("GPSLongitudeRef", "E"))
        if "GPSImgDirection" in g:
            r["heading"] = round(float(g["GPSImgDirection"])) % 360
        if "GPSAltitude" in g:
            r["altitude"] = round(float(g["GPSAltitude"]), 1)
    except (TypeError, ValueError, ZeroDivisionError, IndexError):
        pass
    for k in ("make", "model", "lens", "dto"):
        if isinstance(r[k], bytes):
            r[k] = r[k].decode("utf-8", "replace")
    if r["focal35"] is not None:
        r["focal35"] = int(r["focal35"])
    return r


def _dms(v, ref):
    x = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
    return -x if ref in ("S", "W") else x


NAME_DATES = (
    # WhatsApp: "WhatsApp Image 2026-10-07 at 4.05.09 PM.jpeg" (time optional)
    re.compile(r"(?P<y>20\d\d)-(?P<mo>\d\d)-(?P<d>\d\d)(?: at (?P<h>\d{1,2})\.(?P<mi>\d\d)\.(?P<s>\d\d) (?P<ap>AM|PM))?"),
    # Android and others: IMG_20261008_101112.jpg, PXL_20261009_081500123.jpg
    re.compile(r"(?P<y>20\d\d)(?P<mo>\d\d)(?P<d>\d\d)[_-](?P<h>\d\d)(?P<mi>\d\d)(?P<s>\d\d)"),
    # WhatsApp on Android: IMG-20261007-WA0001.jpg (no time)
    re.compile(r"(?P<y>20\d\d)(?P<mo>\d\d)(?P<d>\d\d)-WA\d+"),
)


def date_of(r):
    """Capture date: EXIF DateTimeOriginal, else a date in the file name. Never the folder or mtime."""
    if r.get("dto"):
        try:
            return datetime.datetime.strptime(r["dto"].strip("\x00 "), "%Y:%m:%d %H:%M:%S"), "exif"
        except ValueError:
            pass
    name = os.path.basename(r["path"])
    for rx in NAME_DATES:
        m = rx.search(name)
        if not m:
            continue
        g = m.groupdict()
        try:
            y, mo, d = int(g["y"]), int(g["mo"]), int(g["d"])
            if not g.get("h"):
                return datetime.datetime(y, mo, d), "file_name"
            hh = int(g["h"])
            if g.get("ap"):
                hh = hh % 12 + (12 if g["ap"] == "PM" else 0)
            return datetime.datetime(y, mo, d, hh, int(g["mi"]), int(g["s"])), "file_name"
        except ValueError:
            continue
    return None, None


def cmd_scan(a):
    folder(a.photos)
    photos, work = os.path.realpath(a.photos), os.path.realpath(a.work)
    if work == photos or work.startswith(photos + os.sep):
        raise Fail("work_inside_photos", "The working folder cannot be the photo folder or lie inside it: "
                   "the photo folder is read only. Choose another working folder.")
    cache = os.path.join(a.work, "cache", "meta.json")
    try:
        prev = load(cache, {}) or {}
    except Fail:  # a corrupt cache is only a cache: rebuild it
        prev = {}
    same = prev.get("version") == META_VERSION and prev.get("photos") == os.path.abspath(a.photos)
    old = {x["path"]: x for x in prev.get("files", [])} if same else {}
    files, skipped = [], collections.Counter()
    for dp, dns, fs in os.walk(a.photos):
        dns.sort()
        for fn in sorted(fs):
            if fn.startswith("."):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, a.photos).replace(os.sep, "/")
            ext = os.path.splitext(fn)[1].lower()
            if ext in VID_EXT:
                skipped["video"] += 1
                continue
            if ext in HEIC_EXT and not HEIC_SUPPORT:
                skipped["heic_unsupported"] += 1
                continue
            if ext not in IMG_EXT | HEIC_EXT:
                skipped["other"] += 1
                continue
            st = os.stat(p)
            o = old.get(rel)
            if o and "error" not in o and o.get("size") == st.st_size and o.get("mtime") == int(st.st_mtime):
                files.append(o)
                continue
            if not readable(p):
                skipped["unreadable"] += 1
                continue
            with open(p, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            r = {"path": rel, "size": st.st_size, "mtime": int(st.st_mtime), "md5": md5}
            try:
                r.update(exif_of(p))
            except ImportError:  # Pillow missing: main() reports how to install it
                raise
            except Exception as e:  # noqa: BLE001 - a broken photo must not stop the scan
                r["error"] = str(e)[:80]
                skipped["cannot_open"] += 1
            d, src = date_of(r)
            r["date"] = d.isoformat() if d else None
            r["date_source"] = src
            files.append(r)
    # duplicates: the first by md5 is canonical; names without " (1)" come first
    files.sort(key=lambda r: (" (" in r["path"], r["path"]))
    seen = {}
    for r in files:
        r["dup_of"] = seen.get(r["md5"])
        seen.setdefault(r["md5"], r["path"])
    save(cache, {"version": META_VERSION, "photos": os.path.abspath(a.photos),
                 "scanned": datetime.datetime.now().isoformat(), "files": files})
    u = [r for r in files if not r["dup_of"] and "error" not in r]
    res = {"images": len(files), "unique": len(u), "duplicates": sum(1 for r in files if r["dup_of"]),
           "undated": [r["path"] for r in u if not r["date"]],
           "dated_from_file_name": [r["path"] for r in u if r.get("date_source") == "file_name"],
           "skipped": dict(skipped)}
    if skipped.get("heic_unsupported"):
        res["hint"] = f"HEIC photos need pillow-heif: {INSTALL}, then scan again"
    out(res)


# ---------------------------------------------------------------- helpers


def meta(work):
    m = load(os.path.join(work, "cache", "meta.json"))
    if not m or m.get("version") != META_VERSION:
        raise Fail("not_scanned", "No up-to-date photo metadata: run scan first")
    return m


def unique(work):
    m = meta(work)
    return m, [r for r in m["files"] if not r.get("dup_of") and "error" not in r and r.get("date")]


def isoweek(r):
    y, w, _ = datetime.datetime.fromisoformat(r["date"]).isocalendar()
    return f"{y}-W{w:02d}"


def is_uw(r):
    lens = (r.get("lens") or "").lower()
    return any(k in lens for k in UW_LENS) or bool(r.get("focal35") and r["focal35"] < UW_FOCAL_35)


def cmd_weeks(a):
    _, u = unique(a.work)
    wk = collections.defaultdict(list)
    for r in u:
        wk[isoweek(r)].append(r)
    res = []
    for k in sorted(wk):
        v = wk[k]
        days = sorted({datetime.datetime.fromisoformat(r["date"]).date() for r in v})
        res.append({"week": k, "photos": len(v), "ultra_wide": sum(map(is_uw, v)),
                    "days": [d.isoformat() for d in days]})
    done = [i["week"] for i in load_reports(a.work)["reports"]]
    out({"weeks": res, "latest": res[-1]["week"] if res else None, "reports_done": done})


def _font(size):
    from PIL import ImageFont

    for ttf in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(ttf, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def thumb(path, tw, th):
    from PIL import Image, ImageOps

    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((tw, th))
    return im


def sheet(items, dest, tw=220, th=390, cols=8, title=None):
    """items: list of (label_lines, abspath). Writes a JPEG contact sheet."""
    from PIL import Image, ImageDraw

    font, big = _font(18), _font(28)
    rows = (len(items) + cols - 1) // cols
    top = 44 if title else 0
    sh = Image.new("RGB", (cols * (tw + 8), top + rows * (th + 52)), "white")
    d = ImageDraw.Draw(sh)
    if title:
        d.text((8, 6), title, fill="black", font=big)
    for i, (lab, p) in enumerate(items):
        x = (i % cols) * (tw + 8)
        y = top + (i // cols) * (th + 52)
        try:
            im = thumb(p, tw, th)
            sh.paste(im, (x + (tw - im.width) // 2, y))
        except Exception:  # noqa: BLE001
            d.text((x + 4, y + 40), "cannot open", fill="red", font=font)
        d.rectangle([x, y, x + 12 + 17 * len(lab[0]), y + 34], fill="black")
        d.text((x + 5, y + 2), lab[0], fill="white", font=big)
        for j, t in enumerate(lab[1:3]):
            d.text((x + 2, y + th + 4 + j * 22), t, fill="black", font=font)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    sh.save(dest, quality=72)
    return os.path.abspath(dest)


def sheets_dir(work):
    return os.path.join(work, "cache", "sheets")


def zone_refs(reports, cfg, before=None):
    """Zones from config.json (else those of the last report). Each zone's reference: the photo
    chosen for it in the latest report before `before`; else the last of its config references."""
    infs = [i for i in reports.get("reports", []) if not before or i["week"] < before]
    zones = cfg.get("zones") or [{"name": x["zone"]} for x in (infs[-1]["slots"] if infs else [])]
    refs = []
    for z in zones:
        ref = {"zone": z["name"], "path": None, "heading": None, "week": None, "source": None}
        for inf in reversed(infs):
            hit = next((x for x in inf["slots"] if x["zone"] == z["name"] and x.get("path")), None)
            if hit:
                ref.update(path=hit["path"], heading=hit.get("heading"), week=inf["week"], source="report")
                break
        if not ref["path"] and z.get("references"):
            ref.update(path=z["references"][-1], source="config")
        refs.append(ref)
    return refs, (infs[-1]["week"] if infs else None)


def _fill_headings(refs, byp):
    for z in refs:
        if z["path"] and z["heading"] is None:
            z["heading"] = byp.get(z["path"], {}).get("heading")


def cmd_candidates(a):
    week_arg(a.week)
    m, u = unique(a.work)
    root = m["photos"]
    v = sorted([r for r in u if isoweek(r) == a.week], key=lambda r: r["date"])
    if not v:
        raise Fail("no_photos_in_week", f"No photos in {a.week}")
    byp = {r["path"]: r for r in m["files"]}
    zones, _ = zone_refs(load_reports(a.work), load_config(a.work), before=a.week)
    _fill_headings(zones, byp)
    zones = [z for z in zones if z["heading"] is not None]
    res = []
    for i, r in enumerate(v):
        c = {"i": i, "path": r["path"], "date": datetime.datetime.fromisoformat(r["date"]).strftime("%Y-%m-%d %H:%M"),
             "ultra_wide": is_uw(r), "vertical": r["h"] >= r["w"], "heading": r.get("heading"),
             "altitude": r.get("altitude"), "camera": r.get("model") or "no EXIF"}
        if zones and r.get("heading") is not None:
            diffs = [(abs((r["heading"] - z["heading"] + 180) % 360 - 180), z["zone"]) for z in zones]
            c["near_heading"] = [z for dlt, z in sorted(diffs) if dlt <= HEADING_TOLERANCE]
        res.append(c)
    sheets = []
    for k in range(0, len(res), a.chunk):
        part = res[k:k + a.chunk]
        items = [([str(c["i"]), f'{c["date"][5:]} {"UW" if c["ultra_wide"] else ""}',
                   f'h{c["heading"] if c["heading"] is not None else "-"} {"V" if c["vertical"] else "H"}'],
                  os.path.join(root, c["path"])) for c in part]
        dest = os.path.join(sheets_dir(a.work), f"{a.week}_candidates_{k // a.chunk + 1}_{STAMP}.jpg")
        sheets.append(sheet(items, dest, title=f"{a.week} · photos {part[0]['i']}-{part[-1]['i']}"))
    out({"week": a.week, "total": len(res), "candidates": res, "sheets": sheets})


def cmd_refsheet(a):
    week_arg(a.week)
    m = meta(a.work)
    refs, last = zone_refs(load_reports(a.work), load_config(a.work), before=a.week)
    byp = {r["path"]: r for r in m["files"]}
    _fill_headings(refs, byp)
    items = [([f"{n + 1}", z["zone"][:22], f'{z["week"] or "config"} h{z["heading"] if z["heading"] is not None else "-"}'],
              os.path.join(m["photos"], z["path"])) for n, z in enumerate(refs) if z["path"]]
    dest = sheet(items, os.path.join(sheets_dir(a.work), f"reference_{last or 'none'}_{STAMP}.jpg"),
                 title=f"Reference per zone (last report: {last or 'none'})") if items else None
    out({"last_report": last, "zones": refs, "without_reference": [z["zone"] for z in refs if not z["path"]],
         "sheet": dest})


def cmd_overview(a):
    """Sheets with EVERY unique photo, numbered in time order (to define the zones)."""
    m, u = unique(a.work)
    u = sorted(u, key=lambda r: r["date"])
    idx = [{"i": i, "path": r["path"], "week": isoweek(r),
            "date": datetime.datetime.fromisoformat(r["date"]).strftime("%Y-%m-%d %H:%M"),
            "ultra_wide": is_uw(r), "heading": r.get("heading")} for i, r in enumerate(u)]
    sheets = []
    for k in range(0, len(idx), a.per):
        part = idx[k:k + a.per]
        items = [([str(c["i"]), f'{c["week"][-3:]} {c["date"][5:10]}{" UW" if c["ultra_wide"] else ""}',
                   f'h{c["heading"] if c["heading"] is not None else "-"}'],
                  os.path.join(m["photos"], c["path"])) for c in part]
        dest = os.path.join(sheets_dir(a.work), f"all_{k // a.per + 1:02d}_{STAMP}.jpg")
        sheets.append(sheet(items, dest, tw=170, th=300, cols=10,
                            title=f"photos {part[0]['i']}-{part[-1]['i']} ({part[0]['week']} to {part[-1]['week']})"))
    index = os.path.join(a.work, "cache", "overview.json")
    save(index, idx)
    out({"photos": len(idx), "index": os.path.abspath(index), "sheets": sheets})


def cmd_choices(a):
    """Choice sheet: per zone, the chosen photo (green) and alternatives A, B, C... (up to 5)."""
    from PIL import Image, ImageDraw

    spec, alts = read_spec(a.spec), load(a.alts, {}) or {}
    txt = {**DEFAULT_LABELS, **(spec.get("labels") or {})}
    m = meta(a.work)
    root, byp = m["photos"], {r["path"]: r for r in m["files"]}
    font, big = _font(18), _font(24)
    tw, th, ncol, hdr = 180, 320, 6, 34
    letters = "ABCDE"
    rows = [(n, sp) for n, sp in enumerate(spec["slots"], 1) if sp.get("path") or alts.get(sp["zone"])]
    empty = [f'{n}. {sp["zone"]}' for n, sp in enumerate(spec["slots"], 1)
             if not sp.get("path") and not alts.get(sp["zone"])]
    foot = 40 if empty else 0
    sh = Image.new("RGB", (16 + ncol * (tw + 10), 50 + len(rows) * (hdr + th + 34) + foot), "white")
    d = ImageDraw.Draw(sh)
    d.text((8, 10), txt["choices_title"].format(week=spec["week"]), fill="black", font=big)
    summary = []
    for r, (n, sp) in enumerate(rows):
        y0 = 50 + r * (hdr + th + 34)
        z = sp["zone"]
        d.text((8, y0 + 2), f"{n}. {z}", fill="black", font=big)
        y = y0 + hdr
        photos = [("✓", sp.get("path"))] + [(letters[k], p) for k, p in enumerate((alts.get(z) or [])[:5])]
        options = {}
        for c, (lab, p) in enumerate(photos):
            x = 8 + c * (tw + 10)
            if p:
                try:
                    im = thumb(os.path.join(root, p), tw, th)
                    sh.paste(im, (x + (tw - im.width) // 2, y))
                except Exception:  # noqa: BLE001
                    d.text((x + 4, y + 40), txt["cannot_open"], fill="red", font=font)
                mp = byp.get(p, {})
                dt = mp.get("date")
                horiz = mp.get("w", 0) > mp.get("h", 1)
                d.text((x + 2, y + th + 6), (dt[5:16].replace("T", " ") if dt else "") + (f'  {txt["cropped"]}' if horiz else ""),
                       fill="#b00020" if horiz else "black", font=font)
            else:
                d.rectangle([x, y, x + tw, y + th], outline="#999999", width=2)
                d.text((x + 30, y + th // 2), txt["no_photo_short"], fill="#666666", font=big)
            if c == 0:
                d.rectangle([x - 3, y - 3, x + tw + 3, y + th + 3], outline="#1a9c3e", width=5)
            d.rectangle([x, y, x + 34, y + 32], fill="#1a9c3e" if c == 0 else "black")
            d.text((x + 8, y + 2), lab, fill="white", font=big)
            if c:
                options[lab] = p
        summary.append({"zone": z, "current": sp.get("path"), "alternatives": options})
    for n, sp in enumerate(spec["slots"], 1):
        if not sp.get("path") and not alts.get(sp["zone"]):
            summary.append({"zone": sp["zone"], "current": None, "alternatives": {}})
    if empty:
        d.text((8, sh.height - foot + 6), txt["no_alternatives"] + " " + ", ".join(empty), fill="#666666", font=font)
    dest = os.path.join(sheets_dir(a.work), f'{spec["week"]}_choices_{STAMP}.jpg')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    sh.save(dest, quality=75)
    out({"sheet": os.path.abspath(dest), "zones": summary})


def read_spec(p):
    spec = load(p)
    if not spec or "slots" not in spec or "week" not in spec:
        raise Fail("bad_spec", f"{p} is missing or has no week and slots")
    week_arg(spec["week"])
    return spec


# ---------------------------------------------------------------- templates

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _rgb(hex_):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(hex_.lstrip("#").upper())


def _color(c):
    if not re.fullmatch(r"#?[0-9A-Fa-f]{6}", c or ""):
        raise Fail("bad_color", f"Colours are hex codes like #0A6E5A, not {c!r}")
    return c.lstrip("#").upper()


def _textbox(slide, x, y, w, h, text, size, bold=False, color="222222", font=None, align=None):
    from pptx.util import Pt

    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    if align is not None:
        p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size, run.font.bold = Pt(size), bold
    run.font.color.rgb = _rgb(color)
    if font:
        run.font.name = font
    return tb


def neutral_template(accent="222222", font="Arial", logo=None, brand=None, card="E9EBED"):
    """The neutral 16:9 template, built from code: no client's layout, logo or authorship."""
    from pptx import Presentation
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Cm, Pt

    prs = Presentation()
    cp = prs.core_properties
    cp.author = cp.last_modified_by = cp.title = cp.comments = cp.subject = cp.keywords = ""
    prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _textbox(s, Cm(1.32), Cm(0.86), Cm(20.32), Cm(0.6), "{{title}}", 10, color="6E6E6E", font=font)
    _textbox(s, Cm(1.32), Cm(1.55), Cm(22.86), Cm(1.2), "{{project}}", 23, bold=True, font=font)
    _textbox(s, Cm(21.0), Cm(0.95), Cm(11.54), Cm(0.55), "{{week}}", 12, bold=True, color=accent,
             font=font, align=PP_ALIGN.RIGHT)
    _textbox(s, Cm(21.0), Cm(1.8), Cm(11.54), Cm(0.5), "{{date}}", 10, color="787878", font=font,
             align=PP_ALIGN.RIGHT)
    line = s.shapes.add_shape(1, Cm(1.32), Cm(3.12), Cm(31.22), Cm(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = _rgb(accent)
    line.line.fill.background()
    area = s.shapes.add_shape(1, Cm(1.32), Cm(3.66), Cm(31.22), Cm(13.89))
    area.fill.solid()
    area.fill.fore_color.rgb = _rgb(card)
    area.line.fill.background()
    area.shadow.inherit = False
    run = area.text_frame.paragraphs[0].add_run()
    run.text = "{{photos}}"
    run.font.size, run.font.bold, run.font.name = Pt(10), True, font
    run.font.color.rgb = _rgb("222222")
    _textbox(s, Cm(1.32), Cm(17.96), Cm(18), Cm(0.5), "{{summary}}", 9, color="828282", font=font)
    if logo:
        from PIL import Image

        try:
            with Image.open(logo) as im:
                ratio = im.width / im.height
        except (OSError, ValueError) as e:
            raise Fail("logo_not_found", f"Cannot open the logo {logo}: {e}") from e
        h = Cm(0.9)
        w = int(h * ratio)
        if w > Cm(8):
            w, h = Cm(8), int(Cm(8) / ratio)
        s.shapes.add_picture(logo, Cm(32.54) - w, Cm(18.3) - h // 2, w, h)
    elif brand:
        _textbox(s, Cm(20.54), Cm(17.85), Cm(12), Cm(0.7), brand, 14, bold=True, font=font,
                 align=PP_ALIGN.RIGHT)
    return prs


def open_deck(path):
    from pptx import Presentation

    if not os.path.isfile(path):
        raise Fail("template_not_found", f"No template at {path}")
    try:
        return Presentation(path)
    except Exception as e:  # noqa: BLE001 - any parse failure means "not a usable .pptx"
        raise Fail("template_unreadable", f"{path} is not a PowerPoint (.pptx) file: {e}") from e


def find_markers(prs):
    if not len(prs.slides):
        return {}
    found = {}
    for sh in prs.slides[0].shapes:
        if sh.has_text_frame:
            for mk in REQUIRED_MARKERS + OPTIONAL_MARKERS:
                if mk in sh.text_frame.text:
                    found.setdefault(mk, sh)
    return found


def check_deck(prs, path):
    found = find_markers(prs)
    missing = [m for m in REQUIRED_MARKERS if m not in found]
    optional = [m for m in OPTIONAL_MARKERS if m not in found]
    if missing:
        raise Fail("template_missing_markers",
                   f"The first slide of {os.path.basename(path)} needs these markers typed into its shapes: "
                   + ", ".join(missing), missing=missing, missing_optional=optional)
    a = found["{{photos}}"]
    return {"missing_optional": optional, "slides": len(prs.slides),
            "photo_area_cm": [round(v / 360000, 2) for v in (a.left, a.top, a.width, a.height)]}


def record_template(work, name="template.pptx"):
    cfg = load_config(work)
    cfg["template"] = name
    cfg.setdefault("version", CONFIG_VERSION)
    save(os.path.join(work, "config.json"), cfg)


def cmd_template(a):
    if a.action == "check":
        out(check_deck(open_deck(a.path), a.path))
        return
    dest = os.path.join(a.work, "template.pptx")
    if a.action == "new":
        accent, card = _color(a.accent), _color(a.card)
        if a.logo and not os.path.isfile(a.logo):
            raise Fail("logo_not_found", f"No logo at {a.logo}")
        neutral_template(accent, a.font, a.logo, a.brand, card).save(dest)
        res = {"template": os.path.abspath(dest), "accent": accent, "font": a.font,
               "logo": bool(a.logo), "brand": a.brand}
    else:  # use
        res = check_deck(open_deck(a.path), a.path)
        if os.path.abspath(a.path) != os.path.abspath(dest):
            shutil.copyfile(a.path, dest)
        res["template"] = os.path.abspath(dest)
    record_template(a.work)
    out(res)


# ---------------------------------------------------------------- build


def _replace(shape, mapping):
    """Swap markers for text, keeping the formatting of each paragraph's first run.
    PowerPoint often splits a marker over several runs, so runs are joined first."""
    for p in shape.text_frame.paragraphs:
        runs = p.runs
        if not runs:
            continue
        full = "".join(r.text for r in runs)
        new = full
        for k, v in mapping.items():
            new = new.replace(k, v)
        if new != full:
            runs[0].text = new
            for r in runs[1:]:
                r._r.getparent().remove(r._r)


def _style(shape):
    """Font of the {{photos}} marker: the style of every label the build writes."""
    run = next((r for p in shape.text_frame.paragraphs for r in p.runs if "{{" in r.text or r.text), None)
    st = {"name": None, "size": 10.0, "bold": False, "color": "222222"}
    if run is not None:
        f = run.font
        st["name"] = f.name
        st["size"] = f.size.pt if f.size else 10.0
        st["bold"] = bool(f.bold)
        try:
            if f.color and f.color.type is not None and f.color.rgb is not None:
                st["color"] = str(f.color.rgb)
        except AttributeError:  # theme colour: no RGB to copy
            pass
    return st


def _photo_bytes(path, ratio):
    from PIL import Image, ImageOps

    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    tw, th = im.size
    if tw / th > ratio:
        nw = int(th * ratio)
        im = im.crop(((tw - nw) // 2, 0, (tw - nw) // 2 + nw, th))
    else:
        nh = int(tw / ratio)
        im = im.crop((0, (th - nh) // 2, tw, (th - nh) // 2 + nh))
    im.thumbnail((900, 1600))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    b.seek(0)
    return b


def render_preview(prs, dest, width=1600):
    """A JPEG of the first slide drawn with Pillow: filled shapes, pictures and text.
    An approximation for checking the layout, not a substitute for PowerPoint."""
    from PIL import Image, ImageDraw

    k = width / prs.slide_width
    im = Image.new("RGB", (width, int(prs.slide_height * k)), "white")
    d = ImageDraw.Draw(im)
    box = lambda sh: [int(sh.left * k), int(sh.top * k), int((sh.left + sh.width) * k), int((sh.top + sh.height) * k)]  # noqa: E731
    for sh in prs.slides[0].shapes:
        if sh.left is None or sh.width is None:
            continue
        b = box(sh)
        if sh.shape_type == 13:  # picture
            try:
                pic = Image.open(io.BytesIO(sh.image.blob)).convert("RGB")
                im.paste(pic.resize((max(1, b[2] - b[0]), max(1, b[3] - b[1]))), (b[0], b[1]))
            except Exception:  # noqa: BLE001
                d.rectangle(b, outline="red")
            continue
        try:
            if sh.fill.type == 1:  # solid
                d.rectangle(b, fill="#" + str(sh.fill.fore_color.rgb))
        except (AttributeError, TypeError, ValueError):
            pass
        if not sh.has_text_frame:
            continue
        y = b[1]
        for p in sh.text_frame.paragraphs:
            text = "".join(r.text for r in p.runs)
            if not text:
                continue
            f0 = p.runs[0].font
            pt = f0.size.pt if f0.size else 10
            px = max(8, int(pt * 12700 * k))
            try:
                color = "#" + str(f0.color.rgb)
            except AttributeError:
                color = "#222222"
            font = _font(px)
            tw = d.textlength(text, font=font)
            x = {2: b[0] + (b[2] - b[0] - tw) / 2, 3: b[2] - tw}.get(int(p.alignment or 1), b[0])
            d.text((x, y), text, fill=color, font=font)
            y += int(px * 1.3)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    im.save(dest, quality=80)
    return os.path.abspath(dest)


def cmd_build(a):
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Cm

    spec = read_spec(a.spec)
    labels = {**DEFAULT_LABELS, **(spec.get("labels") or {})}
    m = meta(a.work)
    root, byp = m["photos"], {r["path"]: r for r in m["files"]}
    slots = spec["slots"]
    n = len(slots)
    if not 1 <= n <= 8:
        raise Fail("bad_slot_count", f"A slide holds 1 to 8 viewpoints, not {n}")
    for sp in slots:
        if sp.get("path") and (sp["path"] not in byp or not os.path.isfile(os.path.join(root, sp["path"]))):
            raise Fail("unknown_photo", f'{sp["path"]} is not among the scanned photos', zone=sp["zone"])
        if sp.get("path"):
            mp = byp[sp["path"]]
            if not mp.get("date") or isoweek(mp) != spec["week"]:
                raise Fail("photo_outside_week", f'{sp["path"]} was not taken in {spec["week"]}'
                           + ("" if mp.get("date") else " (it has no date)"), zone=sp["zone"], path=sp["path"])
    rep = load_reports(a.work)
    known_file = any(i["week"] == spec["week"] and i.get("file") == os.path.basename(a.out) for i in rep["reports"])
    if os.path.exists(a.out) and not a.replace and not known_file:
        raise Fail("output_exists", f"{a.out} already exists and is not this week's report in the history; "
                   "ask the user before replacing it (--replace)")
    cfg = load_config(a.work)
    if cfg.get("template"):
        tpl_path = os.path.join(a.work, cfg["template"])
        prs = open_deck(tpl_path)
        check_deck(prs, tpl_path)
    else:
        prs = neutral_template()
    ids = prs.slides._sldIdLst
    for e in list(ids)[1:]:
        prs.part.drop_rel(e.rId)
        ids.remove(e)
    s = prs.slides[0]
    tree = s.shapes._spTree
    area = find_markers(prs)["{{photos}}"]
    st = _style(area)
    AX, AY, AW, AH = area.left, area.top, area.width, area.height
    proto = area._element
    tree.remove(proto)

    def card(x, y, w, h):
        e = copy.deepcopy(proto)
        ids = [int(i) for i in tree.xpath(".//p:cNvPr/@id")]
        e.xpath("./*[1]/p:cNvPr")[0].set("id", str(max(ids, default=0) + 1))  # a copy keeps the prototype's id
        tree.append(e)
        sh = next(x_ for x_ in s.shapes if x_._element is e)
        sh.left, sh.top, sh.width, sh.height = int(x), int(y), int(w), int(h)
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r._r.getparent().remove(r._r)
        return sh

    k = AH / Cm(13.89)  # sizes follow the neutral template's proportions, scaled to the area
    HDR, CAP, PAD, GAP = Cm(0.95) * k, Cm(0.75) * k, Cm(0.2) * k, Cm(0.254) * k
    OBS_MIN, OBS_GAP = Cm(3.0) * k, Cm(0.35) * k
    ratio = 9 / 16
    pw_max = (AH - OBS_MIN - OBS_GAP - HDR - CAP) * ratio
    w = (AW - GAP * (n - 1)) / n
    pw = min(w - 2 * PAD, pw_max)
    w = pw + 2 * PAD
    ph = pw / ratio
    h = HDR + ph + CAP
    x0 = AX + (AW - (w * n + GAP * (n - 1))) / 2
    size = st["size"] * (1 if n <= 6 else 0.8)
    muted = "96999C"
    latest = None
    for i, sp in enumerate(slots):
        x = x0 + i * (w + GAP)
        card(x, AY, w, h)
        _textbox(s, int(x + PAD), int(AY + Cm(0.3) * k), int(pw), int(HDR - Cm(0.3) * k),
                 f'{i + 1:02d} · {sp["zone"].upper()}', size, st["bold"], st["color"], st["name"])
        cap = ""
        if sp.get("path"):
            s.shapes.add_picture(_photo_bytes(os.path.join(root, sp["path"]), ratio),
                                 int(x + PAD), int(AY + HDR), int(pw), int(ph))
            mp = byp[sp["path"]]
            dt = datetime.datetime.fromisoformat(mp["date"]) if mp.get("date") else None
            if dt:
                cap = dt.strftime(labels["date_format"])
                if mp.get("date_source") == "exif":
                    cap += " · " + dt.strftime(labels["time_format"])
                latest = max(latest, dt) if latest else dt
        else:
            _textbox(s, int(x + PAD), int(AY + HDR + ph / 2 - Cm(0.3) * k), int(pw), int(Cm(0.8) * k),
                     labels["no_photo"], size * 0.9, False, muted, st["name"], PP_ALIGN.CENTER)
        if cap:
            _textbox(s, int(x + PAD), int(AY + HDR + ph + Cm(0.15) * k), int(pw), int(CAP - Cm(0.2) * k),
                     cap, size * 0.8, False, muted, st["name"], PP_ALIGN.RIGHT)
    # observations
    oy = AY + h + OBS_GAP
    card(AX, oy, AW, AY + AH - oy)
    _textbox(s, int(AX + Cm(0.33) * k), int(oy + Cm(0.3) * k), int(AW - Cm(0.66) * k), int(Cm(0.6) * k),
             labels["observations"], st["size"], st["bold"], st["color"], st["name"])
    body = _textbox(s, int(AX + Cm(0.33) * k), int(oy + Cm(0.95) * k), int(AW - Cm(0.66) * k),
                    int(AY + AH - oy - Cm(1.2) * k), "", st["size"], False, "64696E", st["name"])
    tf = body.text_frame
    first = tf.paragraphs[0]
    first.runs[0]._r.getparent().remove(first.runs[0]._r)
    from pptx.util import Pt

    for j, t in enumerate(spec.get("observations") or []):
        p = first if j == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = "· " + t
        run.font.size, run.font.color.rgb = Pt(st["size"]), _rgb("64696E")
        if st["name"]:
            run.font.name = st["name"]
    # header and footer
    year, wk = spec["week"].split("-W")
    date = spec.get("date") or (latest.strftime(labels["date_format"]) if latest else "")
    mapping = {"{{project}}": spec.get("project") or cfg.get("project") or "",
               "{{week}}": labels["week"].format(week=wk, year=year),
               "{{date}}": date, "{{title}}": labels["title"],
               "{{summary}}": labels["summary"].format(n=f"{n:02d}")}
    for sh in s.shapes:
        if sh.has_text_frame:
            _replace(sh, mapping)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    prs.save(a.out)
    preview = render_preview(prs, os.path.join(sheets_dir(a.work), f'preview_{spec["week"]}_{STAMP}.jpg'))
    # history
    entry = {"week": spec["week"], "date": date, "generated": datetime.datetime.now().isoformat(),
             "file": os.path.basename(a.out), "observations": spec.get("observations") or [],
             "slots": [{"zone": sp["zone"], "path": sp.get("path"),
                        "md5": byp.get(sp.get("path"), {}).get("md5"),
                        "heading": byp.get(sp.get("path"), {}).get("heading")} for sp in slots]}
    rep["reports"] = sorted([i for i in rep["reports"] if i["week"] != spec["week"]] + [entry],
                            key=lambda i: i["week"])
    save(os.path.join(a.work, "reports.json"), rep)
    known = [z["name"] for z in cfg.get("zones", [])]
    out({"pptx": os.path.abspath(a.out), "file": os.path.basename(a.out), "preview": preview,
         "viewpoints": n, "date": date,
         "zones_not_in_config": [sp["zone"] for sp in slots if known and sp["zone"] not in known]})


# ---------------------------------------------------------------- main


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Fail("bad_arguments", message)


def parser():
    ap = Parser(prog="site_progress.py")
    sp = ap.add_subparsers(dest="cmd", required=True, parser_class=Parser)
    c = sp.add_parser("check")
    c.add_argument("photos")
    c = sp.add_parser("scan")
    c.add_argument("photos")
    c.add_argument("work")
    c = sp.add_parser("weeks")
    c.add_argument("work")
    c = sp.add_parser("candidates")
    c.add_argument("work")
    c.add_argument("--week", required=True)
    c.add_argument("--chunk", type=int, default=24)
    c = sp.add_parser("overview")
    c.add_argument("work")
    c.add_argument("--per", type=int, default=40)
    c = sp.add_parser("refsheet")
    c.add_argument("work")
    c.add_argument("--week", help="only reports before this week count")
    c = sp.add_parser("choices")
    c.add_argument("work")
    c.add_argument("--spec", required=True)
    c.add_argument("--alts", required=True)
    c = sp.add_parser("build")
    c.add_argument("work")
    c.add_argument("--spec", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--replace", action="store_true", help="replace a file the history does not know")
    t = sp.add_parser("template").add_subparsers(dest="action", required=True, parser_class=Parser)
    c = t.add_parser("new")
    c.add_argument("work")
    c.add_argument("--accent", default="222222")
    c.add_argument("--card", default="E9EBED")
    c.add_argument("--font", default="Arial")
    c.add_argument("--logo")
    c.add_argument("--brand")
    c = t.add_parser("use")
    c.add_argument("work")
    c.add_argument("path")
    c = t.add_parser("check")
    c.add_argument("path")
    sp.add_parser("version")
    return ap


def main(argv=None):
    try:
        a = parser().parse_args(argv)
        if a.cmd == "version":
            out({"version": VERSION})
            return
        globals()["cmd_" + a.cmd](a)
    except Fail as e:
        print(json.dumps({"ok": False, "error": e.code, "message": e.message, **e.extra},
                         ensure_ascii=False, indent=1))
        sys.exit(2)
    except ImportError as e:
        print(json.dumps({"ok": False, "error": "missing_dependency",
                          "message": f"{e.name or e} is not installed", "install": INSTALL}, ensure_ascii=False))
        sys.exit(2)


if __name__ == "__main__":
    main()
