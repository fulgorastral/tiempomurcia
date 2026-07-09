#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga el histórico de valores climatológicos DIARIOS de AEMET OpenData para
Murcia (7178I) y Caravaca de la Cruz (7119B) y genera:

  - murcia_data.js   -> datos que carga Murcia_app_explorador.html
  - aemet_<id>.csv   -> un CSV por estación (por si quieres analizarlos aparte)

La API Key se lee de (por este orden):
  1. La variable de entorno AEMET_API_KEY
  2. El archivo aemet_api_key.txt (junto a este script)

Uso:
  python descargar_aemet_murcia.py             # incremental: solo baja los días nuevos
  python descargar_aemet_murcia.py --completo  # vuelve a bajar toda la serie

No necesita pandas ni requests: solo la librería estándar de Python 3.
"""

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

# Consolas Windows con cp1252: no reventar por emojis/flechas en los print
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))

# ----------------------------- CONFIGURACIÓN -----------------------------
# code: código numérico interno de la app (el listado usa parseInt, no puede llevar letras)
ESTACIONES = [
    {"aemet": "7178I", "code": 7178, "short": "Murcia",
     "name": "Murcia (7178I)", "color": "#e8632a", "desde": "1984-04-01"},
    {"aemet": "7119B", "code": 7119, "short": "Caravaca",
     "name": "Caravaca de la Cruz (7119B)", "color": "#26a69a", "desde": "1984-01-01"},
]

DIAS_POR_BLOQUE = 180          # el endpoint diario admite ~6 meses por petición
PAUSA = 1.5                    # s entre peticiones (límite ~50/min por API Key)
# AEMET devuelve 429 también cuando SU plataforma está saturada ("caudal por minuto"),
# a veces durante muchos minutos seguidos. No es un error: hay que insistir.
MAX_REINTENTOS_429 = 40
SOLAPE_DIAS = 10               # en modo incremental se rebajan estos días para recoger correcciones tardías

SALIDA_JS = os.path.join(AQUI, "murcia_data.js")
BASE = "https://opendata.aemet.es/opendata/api"
# -------------------------------------------------------------------------


def leer_api_key():
    key = os.environ.get("AEMET_API_KEY", "").strip()
    if not key:
        ruta = os.path.join(AQUI, "aemet_api_key.txt")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                # ignora líneas de comentario por si el placeholder sigue ahí
                key = "".join(l.strip() for l in f if l.strip() and not l.startswith("#"))
    if not key or "PEGA" in key.upper():
        sys.exit("⚠️  Falta la API Key. Pégala en aemet_api_key.txt (o exporta AEMET_API_KEY).\n"
                 "    Se consigue gratis en https://opendata.aemet.es/centrodedescargas/obtencionAPIKey")
    return key


API_KEY = None  # se rellena en main()


def _http_get(url):
    """GET crudo con reintentos ante 429/errores de red. Devuelve bytes o None si 404."""
    for intento in range(MAX_REINTENTOS_429 + 1):
        req = urllib.request.Request(url, headers={"api_key": API_KEY, "cache-control": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = int(e.headers.get("Retry-After", 60) or 60)
                print(f"    429: espero {espera}s...", file=sys.stderr)
                time.sleep(espera)
                continue
            if e.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"    Error de red ({e}); reintento en 20s...", file=sys.stderr)
            time.sleep(20)
    raise RuntimeError("Se superaron los reintentos (429/red).")


def get_json(url, allow_404=False):
    """Primera llamada de AEMET: devuelve {estado, datos, ...}. El cuerpo va en ISO-8859-15."""
    raw = _http_get(url)
    if raw is None:
        if allow_404:
            return None
        raise RuntimeError(f"404 en {url}")
    data = json.loads(raw.decode("ISO-8859-15"))
    if isinstance(data, dict):
        estado = data.get("estado", 200)
        if estado == 401:
            sys.exit("⚠️  API Key inválida o caducada (estado 401). Regenera otra con tu email.")
        if estado == 404:
            return None if allow_404 else data
        if estado == 429:
            time.sleep(60)
            return get_json(url, allow_404)
    return data


def get_datos(url_datos):
    """Segunda llamada: la URL temporal 'datos' con el array real."""
    raw = _http_get(url_datos)
    if raw is None:
        return []
    return json.loads(raw.decode("ISO-8859-15"))


def descargar_bloque(indicativo, ini: date, fin: date):
    f_ini = ini.strftime("%Y-%m-%dT00:00:00UTC")
    f_fin = fin.strftime("%Y-%m-%dT23:59:59UTC")
    meta = get_json(f"{BASE}/valores/climatologicos/diarios/datos"
                    f"/fechaini/{f_ini}/fechafin/{f_fin}/estacion/{indicativo}", allow_404=True)
    if not meta or "datos" not in meta:
        return []
    return get_datos(meta["datos"])


def inventario():
    """Metadatos (lat/lon/altitud) de las estaciones, del inventario oficial."""
    print("Consultando inventario de estaciones...")
    meta = get_json(f"{BASE}/valores/climatologicos/inventarioestaciones/todasestaciones")
    if not meta or "datos" not in meta:
        return {}
    todas = get_datos(meta["datos"])
    return {e.get("indicativo"): e for e in todas}


def dms_a_decimal(s):
    """'380007N' -> 38.0019; '011015W' -> -1.1708"""
    if not s or len(s) < 7:
        return None
    try:
        g, m, seg = int(s[0:2]), int(s[2:4]), int(s[4:6])
        dec = g + m / 60 + seg / 3600
        return round(-dec if s[6] in "WS" else dec, 5)
    except ValueError:
        return None


def num(v):
    """AEMET: coma decimal, 'Ip' = inapreciable (<0,1 mm) -> 0, resto no numérico -> None."""
    if v is None:
        return None
    v = str(v).strip()
    if v == "" or v.lower() in ("varias", "acum"):
        return None
    if v == "Ip":
        return 0
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def a_fila(d):
    """Registro AEMET -> fila de la app.
    Índices: 0 fecha, 1 prec, 2 tmin, 3 tmax, 4 tmed, 5 velmedia (m/s), 6 racha (m/s),
    7-8 reservados (QC interno de la app), 9 hrMedia, 10 hrMax, 11 hrMin,
    12-15 reservados (nieve/derivadas), 16 sol (h).
    La app convierte 5 y 6 a km/h al cargar. Se recortan los null finales."""
    fila = [d.get("fecha"),
            num(d.get("prec")), num(d.get("tmin")), num(d.get("tmax")), num(d.get("tmed")),
            num(d.get("velmedia")), num(d.get("racha")),
            None, None,
            num(d.get("hrMedia")), num(d.get("hrMax")), num(d.get("hrMin")),
            None, None, None, None,
            num(d.get("sol"))]
    while len(fila) > 7 and fila[-1] is None:
        fila.pop()
    return fila


def cargar_existente():
    if not os.path.exists(SALIDA_JS):
        return None
    with open(SALIDA_JS, encoding="utf-8") as f:
        txt = f.read()
    m = re.search(r"=\s*(\{.*\})\s*;?\s*$", txt, re.S)
    if not m:
        return None
    try:
        previo = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    # Si el archivo lo generó el plan B (Open-Meteo), no sirve para el modo
    # incremental: hay que bajar la serie AEMET completa y sustituirlo.
    if previo.get("source") != "aemet":
        return None
    return previo


def bloques(inicio: date, fin: date, dias):
    cur = inicio
    while cur <= fin:
        tope = min(cur + timedelta(days=dias - 1), fin)
        yield cur, tope
        cur = tope + timedelta(days=1)


def main():
    global API_KEY
    API_KEY = leer_api_key()
    completo = "--completo" in sys.argv

    previo = None if completo else cargar_existente()
    inv = inventario()
    hoy = date.today()

    salida = {"source": "aemet",
              "fields": ["date", "rr", "tn", "tx", "tm", "ffm", "fxy", "qcflags", "fxy_ms",
                         "um", "ux", "un", "res12", "res13", "tntxm", "fxi", "sol"],
              "stations": [], "data": {}}

    for est in ESTACIONES:
        cod = str(est["code"])
        por_fecha = {}
        desde = datetime.strptime(est["desde"], "%Y-%m-%d").date()

        if previo and cod in previo.get("data", {}) and previo["data"][cod]:
            for fila in previo["data"][cod]:
                por_fecha[fila[0]] = fila
            ultima = max(por_fecha)
            desde = max(desde, datetime.strptime(ultima, "%Y-%m-%d").date() - timedelta(days=SOLAPE_DIAS))
            print(f"\n=== {est['name']}: incremental desde {desde} (ya hay {len(por_fecha)} días) ===")
        else:
            print(f"\n=== {est['name']}: descarga completa desde {desde} (tardará unos minutos) ===")

        pendientes = list(bloques(desde, hoy, DIAS_POR_BLOQUE))
        for pasada in (1, 2, 3):
            if pasada > 1:
                if not pendientes:
                    break
                print(f"  ── Pasada {pasada}: reintento de {len(pendientes)} bloques fallidos ──")
                time.sleep(90)
            fallidos = []
            for i, (ini, fin) in enumerate(pendientes, 1):
                print(f"[{i}/{len(pendientes)}] {ini} → {fin} ...", end=" ")
                try:
                    datos = descargar_bloque(est["aemet"], ini, fin)
                    for d in datos:
                        fila = a_fila(d)
                        if fila[0]:
                            por_fecha[fila[0]] = fila
                    print(f"{len(datos)} días")
                except Exception as e:
                    print(f"ERROR: {e}", file=sys.stderr)
                    fallidos.append((ini, fin))
                time.sleep(PAUSA)
            pendientes = fallidos
        if pendientes:
            sys.exit(f"⚠️  {len(pendientes)} bloques de {est['name']} no se pudieron descargar tras 3 pasadas.\n"
                     "    No escribo nada para no dejar huecos en la serie. Vuelve a intentarlo en un rato\n"
                     "    (AEMET suele estar saturada a mediodía).")

        if not por_fecha:
            print(f"⚠️  Sin datos para {est['name']}; no se incluye.", file=sys.stderr)
            continue

        fechas = sorted(por_fecha)
        filas = [por_fecha[f] for f in fechas]
        info = inv.get(est["aemet"], {})
        alti = num(info.get("altitud"))
        salida["stations"].append({
            "code": est["code"], "name": est["name"], "color": est["color"], "short": est["short"],
            "period": f"{fechas[0][:4]}-{fechas[-1][:4]}",
            "lat": dms_a_decimal(info.get("latitud")), "lon": dms_a_decimal(info.get("longitud")),
            "alti": int(alti) if alti is not None else "?",
            "aemet": est["aemet"],
        })
        salida["data"][cod] = filas

        # CSV por estación (unidades originales de AEMET: viento en m/s)
        ruta_csv = os.path.join(AQUI, f"aemet_{est['aemet']}_diario.csv")
        with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["fecha", "prec_mm", "tmin", "tmax", "tmed",
                        "velmedia_ms", "racha_ms", "hrMedia", "hrMax", "hrMin", "sol_h"])
            for r in filas:
                g = lambda i: r[i] if i < len(r) else None
                w.writerow([r[0], g(1), g(2), g(3), g(4), g(5), g(6), g(9), g(10), g(11), g(16)])
        print(f"    CSV: {os.path.basename(ruta_csv)} ({len(filas)} días, {fechas[0]} → {fechas[-1]})")

    if not salida["stations"]:
        sys.exit("No se ha podido descargar ninguna estación.")

    with open(SALIDA_JS, "w", encoding="utf-8") as f:
        f.write("window.MURCIA_DATA = ")
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    total = sum(len(v) for v in salida["data"].values())
    print(f"\n✅ {os.path.basename(SALIDA_JS)} generado: {len(salida['stations'])} estaciones, {total} días.")
    print("   Abre Murcia_app_explorador.html (o recárgala) para ver los datos.")


if __name__ == "__main__":
    main()
