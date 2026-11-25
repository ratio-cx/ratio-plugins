#!/usr/bin/env python3
"""Search the AEAT (Spanish Tax Agency) list of properties up for auction.

The AEAT publishes every property it is auctioning in one public file,
bienes.js, a JavaScript file that assigns a JSON array of records. The
sandbox this runs in usually cannot download it (outbound traffic goes
through an allowlist), so `fetch` tries once and, failing that, the user
saves the file and `locate` finds it on disk.

Standard library only, Python 3.10+. Every command prints JSON on stdout;
an error is {"ok": false, "error": <code>, "message": ...} with exit code 2.

  aeat_auctions.py fetch
  aeat_auctions.py locate [PATH ...]
  aeat_auctions.py search [--file PATH] [filters] [--compact]
  aeat_auctions.py show ID [--file PATH]
  aeat_auctions.py stats [--file PATH] [filters]
  aeat_auctions.py export --out PATH.csv|PATH.xlsx [--file PATH] [filters]
"""

import argparse
import csv
import datetime as dt
import html
import json
import os
import plistlib
import re
import socket
import statistics
import sys
import tempfile
import unicodedata
import urllib.error
import zipfile
from urllib.request import urlopen
from xml.sax.saxutils import escape as xml_escape

SOURCE_URL = ("https://www2.agenciatributaria.gob.es/static_files/common/internet/"
              "dep/taiif/subastaInmuebles/data2/bienes.js")
APP_BASE = ("https://www2.agenciatributaria.gob.es/static_files/common/internet/"
            "dep/taiif/subastaInmuebles/")
BOE_URL = "https://subastas.boe.es/detalleSubasta.php?idSub={}"
ATTRIBUTION = ("Lista de bienes a subastar por la AEAT a {}. Más información en: "
               "https://sede.agenciatributaria.gob.es/Sede/subastas.html")

# Split so that this file never matches its own search.
VARIABLE = "inmuebles" + "Subasta"
FETCH_TIMEOUT = 10
MAX_BYTES = 20 * 1024 * 1024
MAX_DEPTH = 5
SKIP_DIRS = {"proc", "sys", "dev", "node_modules", "site-packages", "skills", "__pycache__"}
# Where the cloud session puts the files Claude copies from the user's computer.
UPLOAD_ROOTS = ["/mnt/user-data/uploads", "/mnt/user-data"]
# Fields every record has carried; their absence means the AEAT changed the format.
REQUIRED_FIELDS = ("id", "tipo", "codProvincia", "municipioCod", "valoracion", "cargas",
                   "finSubasta")

# Code tables copied from the AEAT search app (aeat2/js/aeat-subastas2.min.js).
TIPOS = {1: "Vivienda", 2: "Local", 3: "Garaje", 4: "Trastero", 5: "Nave industrial",
         6: "Solar", 7: "Finca rústica", 99: "Otros"}
TIPO_ALIASES = {"vivienda": 1, "piso": 1, "casa": 1, "local": 2, "garaje": 3, "parking": 3,
                "plaza": 3, "trastero": 4, "nave": 5, "industrial": 5, "solar": 6,
                "terreno": 6, "finca": 7, "rustica": 7, "otros": 99}
DERECHOS = {1: "Pleno dominio", 2: "Nuda propiedad", 3: "Usufructo",
            4: "Leasing (opción de compra)", 5: "Derecho de superficie",
            6: "Derechos hereditarios", 99: "Otros"}
PROVINCIAS = {1: "Álava", 2: "Albacete", 3: "Alicante", 4: "Almería", 5: "Ávila",
              6: "Badajoz", 7: "Illes Balears", 8: "Barcelona", 9: "Burgos", 10: "Cáceres",
              11: "Cádiz", 12: "Castellón", 13: "Ciudad Real", 14: "Córdoba", 15: "A Coruña",
              16: "Cuenca", 17: "Girona", 18: "Granada", 19: "Guadalajara", 20: "Guipúzcoa",
              21: "Huelva", 22: "Huesca", 23: "Jaén", 24: "León", 25: "Lleida",
              26: "La Rioja", 27: "Lugo", 28: "Madrid", 29: "Málaga", 30: "Murcia",
              31: "Navarra", 32: "Ourense", 33: "Asturias", 34: "Palencia", 35: "Las Palmas",
              36: "Pontevedra", 37: "Salamanca", 38: "Santa Cruz de Tenerife",
              39: "Cantabria", 40: "Segovia", 41: "Sevilla", 42: "Soria", 43: "Tarragona",
              44: "Teruel", 45: "Toledo", 46: "Valencia", 47: "Valladolid", 48: "Vizcaya",
              49: "Zamora", 50: "Zaragoza", 51: "Ceuta", 52: "Melilla"}
PROVINCIA_ALIASES = {"alava": 1, "araba": 1, "baleares": 7, "mallorca": 7, "castello": 12,
                     "coruna": 15, "la coruna": 15, "gipuzkoa": 20, "guipuzcoa": 20,
                     "lerida": 25, "gerona": 17, "orense": 32, "bizkaia": 48,
                     "vizcaya": 48, "rioja": 26, "tenerife": 38, "gran canaria": 35,
                     "navarra": 31, "nafarroa": 31, "alacant": 3}

HERE = os.path.dirname(os.path.abspath(__file__))


class ListError(Exception):
    """A file that cannot be used as the AEAT list; `code` is stable."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def fold(text):
    """Lowercase, strip accents and punctuation, for forgiving comparisons."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def fail(code, message, **extra):
    emit({"ok": False, "error": code, "message": message, **extra})
    sys.exit(2)


def today():
    """Today's date; AEAT_AUCTIONS_TODAY (YYYY-MM-DD) fixes it for tests."""
    fixed = os.environ.get("AEAT_AUCTIONS_TODAY")
    return dt.date.fromisoformat(fixed) if fixed else dt.date.today()


def redact(text):
    """Remove credentials from URLs in an error message (proxy URLs carry them)."""
    return re.sub(r"(\w+://)[^/\s@]+@", r"\1***@", str(text))


# --- Reading the file -------------------------------------------------------

def decode(raw):
    """The text of the list, from the file as saved: plain, web archive or HTML."""
    if raw.startswith(b"bplist"):
        try:
            archive = plistlib.loads(raw)
            raw = archive["WebMainResource"]["WebResourceData"]
        except (plistlib.InvalidFileException, KeyError, TypeError, ValueError):
            raise ListError("not_aeat_file", "es un archivo web de Safari que no contiene la lista")
    text = raw.decode("utf-8", errors="replace")
    if VARIABLE in text and "&quot;" in text:
        text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return text


def parse_text(body):
    """Return (version, items) from the text of a bienes.js, or raise ListError."""
    at = body.find(VARIABLE)
    if at < 0:
        raise ListError("not_aeat_file", "no es la lista de bienes de la AEAT (bienes.js)")
    start = body.find("[", at)
    if start < 0:
        raise ListError("truncated", "la lista está incompleta (¿descarga cortada?)")
    try:
        # Decode the array itself: a "];" inside a description must not end it early.
        items, _ = json.JSONDecoder().raw_decode(body, start)
    except json.JSONDecodeError as e:
        if body.find("];", start) < 0:
            raise ListError("truncated", "la lista está incompleta (¿descarga cortada?)")
        raise ListError("format_changed", "la lista no se puede leer como JSON: %s" % e)
    if not isinstance(items, list) or not items:
        raise ListError("format_changed", "la lista no contiene ningún bien")
    for item in items:
        if not isinstance(item, dict):
            raise ListError("format_changed", "la lista no es una serie de bienes")
        missing = [f for f in REQUIRED_FIELDS if f not in item]
        if missing:
            raise ListError("format_changed",
                            "la AEAT ha cambiado el formato: faltan los campos %s"
                            % ", ".join(missing))
    m = re.search(r"Version:\s*(\d{8})\s+(\d{2}:\d{2}:\d{2})", body[:at])
    if m:
        d = m.group(1)
        version = "%s-%s-%s %s" % (d[:4], d[4:6], d[6:], m.group(2))
    else:
        m = re.search(r"fechaBienesSubasta\s*=\s*\(new Date\('(\d{4}-\d{2}-\d{2})'\)", body)
        version = m.group(1) if m else None
    return version, items


def parse_file(path):
    with open(path, "rb") as fh:
        raw = fh.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ListError("not_aeat_file", "el fichero es demasiado grande para ser la lista")
    return parse_text(decode(raw))


def cache_dirs():
    """Where fetch keeps the list: the user cache, else the temp dir. Searched in this order."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return [os.path.join(base, "ratio-aeat-auctions"),
            os.path.join(tempfile.gettempdir(), "ratio-aeat-auctions")]


def candidate_roots(extra):
    home = os.path.expanduser("~")
    roots = list(extra)
    mnt = os.path.join(home, "mnt")
    roots += [mnt] + UPLOAD_ROOTS + cache_dirs() + [os.getcwd(), home]
    seen, out = set(), []
    for r in roots:
        r = os.path.realpath(r)
        if r not in seen and os.path.exists(r):
            seen.add(r)
            out.append(r)
    return out


def iter_files(root):
    if os.path.isfile(root):
        yield root
        return
    base = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        if dirpath.count(os.sep) - base >= MAX_DEPTH:
            dirs[:] = []
        for f in files:
            yield os.path.join(dirpath, f)


def looks_like_list(path):
    try:
        size = os.path.getsize(path)
        if size < 100 or size > MAX_BYTES:
            return False
        with open(path, "rb") as fh:
            return VARIABLE.encode() in fh.read()
    except OSError:
        return False


def find_files(extra):
    found, seen = [], {os.path.realpath(__file__)}
    for root in candidate_roots(extra):
        for p in iter_files(root):
            p = os.path.realpath(p)
            if p in seen:
                continue
            seen.add(p)
            if not looks_like_list(p):
                continue
            entry = {"path": p, "bytes": os.path.getsize(p)}
            try:
                entry["version"], items = parse_file(p)
                entry["n_bienes"] = len(items)
                entry["ok"] = True
            except (OSError, ListError) as e:
                entry["ok"] = False
                entry["error"] = getattr(e, "code", "unreadable")
                entry["problem"] = str(e)
            found.append(entry)
    good = [f for f in found if f["ok"]]
    good.sort(key=lambda f: (f.get("version") or "", os.path.getmtime(f["path"])), reverse=True)
    return found, (good[0] if good else None)


def age_days(version):
    if not version:
        return None
    return (today() - dt.date.fromisoformat(version[:10])).days


def load(path):
    if path:
        try:
            version, items = parse_file(path)
        except OSError as e:
            fail("bad_file", "No puedo leer %s: %s" % (path, e), source_url=SOURCE_URL)
        except ListError as e:
            fail(e.code, "%s: %s" % (path, e.message), source_url=SOURCE_URL)
        return path, version, items
    found, best = find_files([])
    if not best and found:
        broken = found[0]
        fail(broken["error"], "Hay una copia de la lista pero no se puede usar: %s"
             % broken["problem"], file=broken["path"], source_url=SOURCE_URL)
    if not best:
        fail("file_not_found", "No encuentro ninguna copia de la lista de la AEAT (bienes.js).",
             source_url=SOURCE_URL)
    version, items = parse_file(best["path"])
    return best["path"], version, items


def attribution(version):
    if not version:
        return ATTRIBUTION.format("fecha desconocida")
    y, m, d = version[:10].split("-")
    return ATTRIBUTION.format("%s/%s/%s" % (d, m, y))


def header(path, version):
    return {"ok": True, "file": path, "version": version, "age_days": age_days(version),
            "atribucion": attribution(version)}


# --- Presenting a property ---------------------------------------------------

_municipios = None


def municipio(code):
    global _municipios
    if _municipios is None:
        try:
            with open(os.path.join(HERE, "municipios.json"), encoding="utf-8") as fh:
                _municipios = json.load(fh)
        except OSError:
            _municipios = {}
    return _municipios.get(str(code))


def money(value):
    return round(value or 0, 2)


# Narrow on purpose: a timeshare week sold as if it were a flat. Read from the description,
# because the AEAT records it as full ownership of 100 %.
TIMESHARE = re.compile(r"\b(multipropiedad|aprovechamiento por turnos?|tiempo compartido"
                       r"|semanas? (numero|n) )")


def warnings(item):
    out = []
    if item.get("derecho") != 1:
        out.append("derecho_no_pleno")
    if (item.get("porcTitularidad") or 0) < 100:
        out.append("titularidad_parcial")
    if (item.get("cargas") or 0) > 0:
        out.append("con_cargas")
    if TIMESHARE.search(fold(item.get("descripcion") or "") + " "):
        out.append("posible_multipropiedad")
    return out


def describe(item, full=False):
    fotos = item.get("fotos") or []
    out = {
        "id": item["id"],
        "tipo": TIPOS.get(item.get("tipo"), "Otros"),
        "derecho": DERECHOS.get(item.get("derecho"), "Otros"),
        "porc_titularidad": item.get("porcTitularidad"),
        "provincia": PROVINCIAS.get(item.get("codProvincia")),
        "municipio": municipio(item.get("municipioCod")),
        "cp": "%05d" % item["cp"] if item.get("cp") else None,
        "direccion": item.get("direccion"),
        "valoracion_eur": money(item.get("valoracion")),
        "cargas_eur": money(item.get("cargas")),
        "neto_eur": money((item.get("valoracion") or 0) - (item.get("cargas") or 0)),
        "fin_subasta": item.get("finSubasta"),
        "avisos": warnings(item),
        "ref_catastral": item.get("refCatastro") or None,
        "subasta_boe": item.get("subasta"),
        "url_boe": BOE_URL.format(item["subasta"]) if item.get("subasta") else None,
        "url_aeat": APP_BASE + "index.html#/inmueble/" + item["id"],
        "n_fotos": len(fotos),
    }
    if full:
        out["subasta_cerrada"] = not is_open(item)
        out["descripcion"] = item.get("descripcion")
        out["cru"] = item.get("cru") or None
        out["gps"] = ([item["gpsLat"], item["gpsLong"]]
                      if item.get("gpsLat") is not None else None)
        out["fotos"] = [APP_BASE + "data2/%s/%s" % (item["id"], f) for f in fotos]
    else:
        desc = item.get("descripcion") or ""
        out["descripcion_corta"] = desc[:200] + ("…" if len(desc) > 200 else "")
    return out


COMPACT = ("id", "tipo", "derecho", "porc_titularidad", "municipio", "provincia", "valoracion_eur", "cargas_eur", "neto_eur",
           "fin_subasta", "avisos", "url_aeat")


def compact(item):
    full = describe(item)
    return {k: full[k] for k in COMPACT}


# --- Filters -----------------------------------------------------------------

def resolve_provincia(value):
    if value.strip().isdigit():
        code = int(value)
        if code in PROVINCIAS:
            return code
    key = fold(value)
    if key in PROVINCIA_ALIASES:
        return PROVINCIA_ALIASES[key]
    for code, name in PROVINCIAS.items():
        if fold(name) == key:
            return code
    fail("unknown_province", "Provincia desconocida: %s" % value,
         valid=sorted(PROVINCIAS.values()))


def resolve_tipos(values):
    codes = set()
    for v in values:
        for part in v.split(","):
            key = fold(part)
            if not key:
                continue
            if key.isdigit() and int(key) in TIPOS:
                codes.add(int(key))
            elif key in TIPO_ALIASES:
                codes.add(TIPO_ALIASES[key])
            else:
                fail("unknown_type", "Tipo desconocido: %s" % part,
                     valid=sorted(TIPO_ALIASES))
    return codes


def matches(item, a, tipos, provincia):
    if provincia is not None and item.get("codProvincia") != provincia:
        return False
    if a.municipio and fold(a.municipio) not in fold(municipio(item.get("municipioCod")) or ""):
        return False
    if a.cp and ("%05d" % (item.get("cp") or 0)) != a.cp.strip().zfill(5):
        return False
    if tipos and item.get("tipo") not in tipos:
        return False
    if a.solo_pleno_dominio and {"derecho_no_pleno", "titularidad_parcial"} & set(warnings(item)):
        return False
    val = item.get("valoracion") or 0
    if a.precio_min is not None and val < a.precio_min:
        return False
    if a.precio_max is not None and val > a.precio_max:
        return False
    cargas = item.get("cargas") or 0
    if a.sin_cargas and cargas > 0:
        return False
    if a.cargas_max is not None and cargas > a.cargas_max:
        return False
    if a.cierre_hasta and (item.get("finSubasta") or "9999") > a.cierre_hasta:
        return False
    if a.con_ref_catastral and not item.get("refCatastro"):
        return False
    if a.texto and fold(a.texto) not in fold(
            (item.get("descripcion") or "") + " " + (item.get("direccion") or "")):
        return False
    return True


SORTS = {
    "valoracion": lambda i: i.get("valoracion") or 0,
    "cargas": lambda i: i.get("cargas") or 0,
    "cierre": lambda i: i.get("finSubasta") or "",
    "neto": lambda i: (i.get("valoracion") or 0) - (i.get("cargas") or 0),
}


def is_open(item):
    """Still open today. A record without a closing date is not presented as open."""
    return bool(item.get("finSubasta")) and item["finSubasta"] >= today().isoformat()


def open_auctions(items):
    return [i for i in items if is_open(i)]


def select(a):
    """Load the list and apply the filters; return (path, version, items, open, hits)."""
    path, version, items = load(a.file)
    tipos = resolve_tipos(a.tipo) if a.tipo else set()
    provincia = resolve_provincia(a.provincia) if a.provincia else None
    still_open = open_auctions(items)
    hits = [i for i in still_open if matches(i, a, tipos, provincia)]
    hits.sort(key=SORTS[a.orden], reverse=a.desc)
    return path, version, items, still_open, hits


def by_province(items):
    counts = {}
    for i in items:
        name = PROVINCIAS.get(i.get("codProvincia"), "Desconocida")
        counts[name] = counts.get(name, 0) + 1
    return [{"provincia": k, "subastas_abiertas": v}
            for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


# --- Commands ----------------------------------------------------------------

def cmd_fetch(a):
    for folder in cache_dirs():
        target = os.path.join(folder, "bienes.js")
        if not os.path.isfile(target):
            continue
        try:
            version, items = parse_file(target)
        except (OSError, ListError):
            continue
        if age_days(version) == 0:
            emit({**header(target, version), "descargado": False, "n_bienes": len(items)})
            return
    try:
        with urlopen(SOURCE_URL, timeout=FETCH_TIMEOUT) as resp:
            raw = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        fail("http_error", "La AEAT respondió %s al descargar la lista." % e.code,
             source_url=SOURCE_URL)
    except (socket.timeout, TimeoutError):
        fail("network_timeout", "La descarga no terminó en %s s." % FETCH_TIMEOUT,
             source_url=SOURCE_URL)
    except urllib.error.URLError as e:
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            fail("network_timeout", "La descarga no terminó en %s s." % FETCH_TIMEOUT,
                 source_url=SOURCE_URL)
        fail("network_blocked", "Este entorno no puede conectar con la AEAT (%s)."
             % redact(e.reason), source_url=SOURCE_URL)
    except OSError as e:
        fail("network_blocked", "Este entorno no puede conectar con la AEAT (%s)." % redact(e),
             source_url=SOURCE_URL)
    try:
        version, items = parse_text(decode(raw))
    except ListError as e:
        code = "format_changed" if e.code == "not_aeat_file" else e.code
        fail(code, "La descarga no es una lista utilizable: %s" % e.message,
             source_url=SOURCE_URL)
    for folder in cache_dirs():
        try:
            os.makedirs(folder, exist_ok=True)
            target = os.path.join(folder, "bienes.js")
            with open(target + ".part", "wb") as fh:
                fh.write(raw)
            os.replace(target + ".part", target)
            break
        except OSError:
            continue
    else:
        fail("cache_unwritable", "Descargada, pero no hay ninguna carpeta donde guardarla.")
    emit({**header(target, version), "descargado": True, "n_bienes": len(items)})


def cmd_locate(a):
    found, best = find_files(a.paths)
    result = {"ok": bool(best), "source_url": SOURCE_URL, "files": found,
              "best": best["path"] if best else None,
              "version": best["version"] if best else None,
              "age_days": age_days(best["version"]) if best else None}
    if not best:
        result["error"] = "file_not_found"
    emit(result)


def cmd_search(a):
    path, version, items, still_open, hits = select(a)
    shown = hits[:a.limit]
    out = {**header(path, version),
           "total_en_fichero": len(items),
           "cerradas_descartadas": sum(1 for i in items if i.get("finSubasta") and not is_open(i)),
           "sin_fecha_descartadas": sum(1 for i in items if not i.get("finSubasta")),
           "coincidencias": len(hits),
           "mostradas": len(shown),
           "resultados": [compact(i) if a.compact else describe(i) for i in shown]}
    if not hits:
        out["provincias_con_subastas"] = by_province(still_open)
    emit(out)


def cmd_show(a):
    path, version, items = load(a.file)
    found = [i for i in items if i["id"] == a.id or i.get("subasta") == a.id]
    if not found:
        fail("not_found", "No hay ningún bien con id o subasta %s en la lista del %s"
             % (a.id, version))
    emit({**header(path, version), "bienes": [describe(i, full=True) for i in found]})


def summary(items, key, label):
    groups = {}
    for i in items:
        groups.setdefault(key(i), []).append(i)
    rows = []
    for name, group in groups.items():
        values = [i.get("valoracion") or 0 for i in group]
        rows.append({label: name, "n": len(group),
                     "sin_cargas": sum(1 for i in group if not (i.get("cargas") or 0)),
                     "valoracion_min": money(min(values)),
                     "valoracion_mediana": money(statistics.median(values)),
                     "valoracion_max": money(max(values))})
    rows.sort(key=lambda r: (-r["n"], r[label]))
    return rows


def cmd_stats(a):
    path, version, items, still_open, hits = select(a)
    emit({**header(path, version), "total": len(hits),
          "cerradas_descartadas": len(items) - len(still_open),
          "por_provincia": summary(hits, lambda i: PROVINCIAS.get(i.get("codProvincia"),
                                                                  "Desconocida"), "provincia"),
          "por_tipo": summary(hits, lambda i: TIPOS.get(i.get("tipo"), "Otros"), "tipo")})


EXPORT_COLUMNS = ("id", "tipo", "derecho", "porc_titularidad", "provincia", "municipio", "cp",
                  "direccion", "valoracion_eur", "cargas_eur", "neto_eur", "fin_subasta",
                  "avisos", "ref_catastral", "subasta_boe", "url_aeat", "url_boe",
                  "descripcion_corta")


FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value):
    """Text a spreadsheet would run as a formula gets a leading apostrophe."""
    if isinstance(value, str) and value.startswith(FORMULA_START):
        return "'" + value
    return value


def export_rows(hits):
    for item in hits:
        d = describe(item)
        d["avisos"] = ", ".join(d["avisos"])
        yield [d[c] for c in EXPORT_COLUMNS]


def column_name(n):
    name = ""
    while n:
        n, r = divmod(n - 1, 26)
        name = chr(65 + r) + name
    return name


def write_xlsx(path, columns, rows):
    """A minimal one-sheet workbook, stdlib only: inline strings and numbers."""
    def cell(ref, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return '<c r="%s"><v>%s</v></c>' % (ref, value)
        if value is None:
            return ""
        return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (
            ref, xml_escape(str(value)))

    lines = []
    for r, row in enumerate([list(columns)] + [list(x) for x in rows], start=1):
        cells = "".join(cell("%s%d" % (column_name(c), r), v) for c, v in enumerate(row, 1))
        lines.append('<row r="%d">%s</row>' % (r, cells))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData>%s</sheetData></worksheet>' % "".join(lines))
    parts = {
        "[Content_Types].xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>',
        "_rels/.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        "xl/workbook.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Subastas" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>',
        "xl/worksheets/sheet1.xml": sheet,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in parts.items():
            z.writestr(name, content)


def cmd_export(a):
    ext = os.path.splitext(a.out)[1].lower()
    if ext not in (".csv", ".xlsx"):
        fail("bad_format", "Exporto a .csv o .xlsx, no a %s" % (ext or "un fichero sin extensión"))
    path, version, _, _, hits = select(a)
    rows = list(export_rows(hits))
    try:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        if ext == ".csv":
            with open(a.out, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(EXPORT_COLUMNS)
                writer.writerows([csv_safe(v) for v in row] for row in rows)
        else:
            write_xlsx(a.out, EXPORT_COLUMNS, rows)
    except OSError as e:
        fail("cannot_write", "No puedo escribir %s: %s" % (a.out, e))
    emit({**header(path, version), "out": os.path.abspath(a.out), "filas": len(rows)})


def add_filters(p):
    p.add_argument("--file", help="bienes.js to use (default: the newest copy found)")
    p.add_argument("--provincia", help="Name, alias (Bizkaia, Lleida...) or INE code")
    p.add_argument("--municipio", help="Part of the municipality name")
    p.add_argument("--cp", help="Postal code")
    p.add_argument("--tipo", action="append",
                   help="vivienda, local, garaje, trastero, nave, solar, finca, otros; "
                        "repeatable or comma-separated")
    p.add_argument("--solo-pleno-dominio", action="store_true",
                   help="Only full ownership of 100%%")
    p.add_argument("--precio-min", type=float, help="Minimum valuation, EUR")
    p.add_argument("--precio-max", type=float, help="Maximum valuation, EUR")
    p.add_argument("--sin-cargas", action="store_true", help="Only without encumbrances")
    p.add_argument("--cargas-max", type=float, help="Maximum encumbrances, EUR")
    p.add_argument("--cierre-hasta", help="Closing on or before YYYY-MM-DD")
    p.add_argument("--con-ref-catastral", action="store_true")
    p.add_argument("--texto", help="Part of the description or address")
    p.add_argument("--orden", choices=sorted(SORTS), default="cierre")
    p.add_argument("--desc", action="store_true", help="Sort descending")


class Parser(argparse.ArgumentParser):
    """Argument errors in the same JSON shape as every other error."""

    def error(self, message):
        fail("bad_arguments", message, usage=self.format_usage().strip())


def main(argv=None):
    p = Parser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("fetch", help="Try to download the list into a cache")
    pf.set_defaults(func=cmd_fetch)

    pl = sub.add_parser("locate", help="Find the newest copy of the list on disk")
    pl.add_argument("paths", nargs="*", help="Extra files or folders to look in")
    pl.set_defaults(func=cmd_locate)

    ps = sub.add_parser("search", help="Filter the open auctions")
    add_filters(ps)
    ps.add_argument("--limit", type=int, default=20)
    ps.add_argument("--compact", action="store_true", help="One short record per property")
    ps.set_defaults(func=cmd_search)

    pw = sub.add_parser("show", help="Full record of a property or of every lot of an auction")
    pw.add_argument("id", help="Property id or SUB-AT-... auction id")
    pw.add_argument("--file")
    pw.set_defaults(func=cmd_show)

    pt = sub.add_parser("stats", help="Counts and valuation ranges by province and type")
    add_filters(pt)
    pt.set_defaults(func=cmd_stats)

    pe = sub.add_parser("export", help="Write the matching auctions to CSV or Excel")
    add_filters(pe)
    pe.add_argument("--out", required=True, help="Destination .csv or .xlsx")
    pe.set_defaults(func=cmd_export)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
