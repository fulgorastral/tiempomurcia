#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga la OBSERVACIÓN en tiempo real de AEMET para Murcia (7178I) y Caravaca
de la Cruz (7119B) y genera observacion.js con el dato de ahora mismo.

Ojo, no confundir con descargar_aemet_murcia.py:
  · Ese baja los VALORES CLIMATOLÓGICOS DIARIOS: datos validados, definitivos,
    pero publicados con 2-4 días de retraso. Son los de la gráfica.
  · Este baja la OBSERVACIÓN horaria: el dato de hace un rato, sin validar.
    Solo devuelve las últimas ~24 horas, así que no sirve para el histórico:
    únicamente alimenta el panel de "ahora mismo".

El archivo generado NO se versiona (está en .gitignore): lo regenera el robot
en cada pasada horaria y viaja directamente a la web publicada.

Uso:  python descargar_observacion.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "observacion.js")
BASE = "https://opendata.aemet.es/opendata/api"

ESTACIONES = [
    {"aemet": "7178I", "code": 7178, "short": "Murcia", "color": "#e8632a"},
    {"aemet": "7119B", "code": 7119, "short": "Caravaca", "color": "#26a69a"},
]


def leer_api_key():
    key = os.environ.get("AEMET_API_KEY", "").strip()
    if not key:
        ruta = os.path.join(AQUI, "aemet_api_key.txt")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                key = "".join(l.strip() for l in f if l.strip() and not l.startswith("#"))
    if not key or "PEGA" in key.upper():
        sys.exit("⚠️  Falta la API Key (AEMET_API_KEY o aemet_api_key.txt).")
    return key


API_KEY = None


def _get(url, cabecera=False):
    for intento in range(4):
        req = urllib.request.Request(url, headers={"api_key": API_KEY} if cabecera else {})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", 30) or 30))
                continue
            if e.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10)
    return None


def observacion(indicativo):
    raw = _get(f"{BASE}/observacion/convencional/datos/estacion/{indicativo}", cabecera=True)
    if not raw:
        return []
    meta = json.loads(raw.decode("ISO-8859-15"))
    if not isinstance(meta, dict) or "datos" not in meta:
        return []
    datos = _get(meta["datos"])
    return json.loads(datos.decode("ISO-8859-15")) if datos else []


def num(regs, campo, func):
    """Aplica func (max/min/sum) sobre los valores numéricos presentes."""
    vals = [r[campo] for r in regs if isinstance(r.get(campo), (int, float))]
    return round(func(vals), 1) if vals else None


def main():
    global API_KEY
    API_KEY = leer_api_key()
    salida = {"generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "estaciones": []}

    for est in ESTACIONES:
        regs = observacion(est["aemet"])
        # Solo sirven los registros con temperatura; el último es el más reciente
        con_ta = [r for r in regs if isinstance(r.get("ta"), (int, float))]
        if not con_ta:
            print(f"  {est['short']}: sin observación disponible", file=sys.stderr)
            continue
        u = con_ta[-1]
        # La ventana que devuelve AEMET es de ~24 h, pero varía: decimos cuánta hay
        try:
            t0 = datetime.strptime(con_ta[0]["fint"], "%Y-%m-%dT%H:%M:%S%z")
            t1 = datetime.strptime(u["fint"], "%Y-%m-%dT%H:%M:%S%z")
            horas = max(1, round((t1 - t0).total_seconds() / 3600))
        except (ValueError, KeyError):
            horas = len(con_ta)

        ms_a_kmh = lambda v: round(v * 3.6, 1) if isinstance(v, (int, float)) else None
        salida["estaciones"].append({
            "code": est["code"], "short": est["short"], "color": est["color"],
            "ubi": (u.get("ubi") or "").strip().title(),
            "fint": u.get("fint"),
            "ta": u.get("ta"),
            "hr": u.get("hr"),
            "prec": num(con_ta, "prec", sum),
            "vv": ms_a_kmh(u.get("vv")),
            "vmax": ms_a_kmh(num(con_ta, "vmax", max)),
            "tamax": num(con_ta, "tamax", max),
            "tamin": num(con_ta, "tamin", min),
            "horas": horas,
        })
        print(f"  {est['short']}: {u.get('ta')} °C a las {u.get('fint')} "
              f"({len(con_ta)} registros, ventana {horas} h)")

    if not salida["estaciones"]:
        sys.exit("No se ha podido leer la observación de ninguna estación.")

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("// Observación en tiempo real de AEMET (sin validar). "
                "Lo regenera descargar_observacion.py en cada pasada horaria.\n")
        f.write("window.OBSERVACION = ")
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"✅ {os.path.basename(SALIDA)} generado.")


if __name__ == "__main__":
    main()
