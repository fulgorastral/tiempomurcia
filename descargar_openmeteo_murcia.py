#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plan B: descarga la serie diaria 1984-hoy de Open-Meteo (reanálisis ERA5) para
Murcia y Caravaca de la Cruz y genera murcia_data.js + un CSV por localidad.

No necesita API Key y responde en segundos. Son datos de MODELO (reanálisis),
no las medidas oficiales de las estaciones AEMET: valen para explorar, pero para
algo formal usa descargar_aemet_murcia.py (cuando AEMET responda, ese script
sobreescribirá estos datos con los oficiales automáticamente).

Uso:  python descargar_openmeteo_murcia.py
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA_JS = os.path.join(AQUI, "murcia_data.js")

LUGARES = [
    {"code": 7178, "short": "Murcia", "name": "Murcia (ERA5, prov.)",
     "color": "#e8632a", "lat": 38.0019, "lon": -1.1708, "alti": 62, "desde": "1984-04-01"},
    {"code": 7119, "short": "Caravaca", "name": "Caravaca de la Cruz (ERA5, prov.)",
     "color": "#26a69a", "lat": 38.1067, "lon": -1.8622, "alti": 625, "desde": "1984-01-01"},
]

DAILY = ("temperature_2m_min,temperature_2m_max,temperature_2m_mean,precipitation_sum,"
         "windspeed_10m_mean,windgusts_10m_max,relative_humidity_2m_mean,"
         "relative_humidity_2m_max,relative_humidity_2m_min,sunshine_duration")


def pedir(lugar, fin):
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lugar['lat']}&longitude={lugar['lon']}"
           f"&start_date={lugar['desde']}&end_date={fin}"
           f"&daily={DAILY}&windspeed_unit=ms&timezone=Europe%2FMadrid")
    for intento in range(5):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  Error ({e}); reintento en 15s...", file=sys.stderr)
            time.sleep(15)
    raise RuntimeError("Open-Meteo no responde.")


def main():
    fin = (date.today() - timedelta(days=6)).isoformat()  # ERA5 va con ~5 días de retraso
    salida = {"source": "open-meteo",
              "fields": ["date", "rr", "tn", "tx", "tm", "ffm", "fxy", "qcflags", "fxy_ms",
                         "um", "ux", "un", "res12", "res13", "tntxm", "fxi", "sol"],
              "stations": [], "data": {}}

    for lugar in LUGARES:
        print(f"=== {lugar['name']}: {lugar['desde']} → {fin} ===")
        js = pedir(lugar, fin)
        d = js.get("daily", {})
        fechas = d.get("time", [])
        if not fechas:
            sys.exit(f"Open-Meteo no ha devuelto datos para {lugar['name']}.")
        col = lambda k: d.get(k) or [None] * len(fechas)
        tn, tx, tm = col("temperature_2m_min"), col("temperature_2m_max"), col("temperature_2m_mean")
        rr, ffm, fxy = col("precipitation_sum"), col("windspeed_10m_mean"), col("windgusts_10m_max")
        um, ux, un = col("relative_humidity_2m_mean"), col("relative_humidity_2m_max"), col("relative_humidity_2m_min")
        sol = col("sunshine_duration")
        filas = []
        for i, f in enumerate(fechas):
            s = sol[i]
            fila = [f, rr[i], tn[i], tx[i], tm[i], ffm[i], fxy[i], None, None,
                    um[i], ux[i], un[i], None, None, None, None,
                    round(s / 3600, 1) if s is not None else None]
            while len(fila) > 7 and fila[-1] is None:
                fila.pop()
            filas.append(fila)
        salida["stations"].append({
            "code": lugar["code"], "name": lugar["name"], "color": lugar["color"],
            "short": lugar["short"], "period": f"{fechas[0][:4]}-{fechas[-1][:4]}",
            "lat": lugar["lat"], "lon": lugar["lon"], "alti": lugar["alti"],
        })
        salida["data"][str(lugar["code"])] = filas

        ruta_csv = os.path.join(AQUI, f"openmeteo_{lugar['short'].lower()}_diario.csv")
        with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["fecha", "prec_mm", "tmin", "tmax", "tmed",
                        "velmedia_ms", "racha_ms", "hrMedia", "hrMax", "hrMin", "sol_h"])
            for r in filas:
                g = lambda i: r[i] if i < len(r) else None
                w.writerow([r[0], g(1), g(2), g(3), g(4), g(5), g(6), g(9), g(10), g(11), g(16)])
        print(f"  {len(filas)} días ({fechas[0]} → {fechas[-1]}) · CSV: {os.path.basename(ruta_csv)}")

    with open(SALIDA_JS, "w", encoding="utf-8") as f:
        f.write("window.MURCIA_DATA = ")
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"\n✅ {os.path.basename(SALIDA_JS)} generado (fuente provisional: Open-Meteo/ERA5).")
    print("   Abre Murcia_app_explorador.html. Cuando AEMET vuelva, descargar_aemet_murcia.py lo sustituirá por datos oficiales.")


if __name__ == "__main__":
    main()
