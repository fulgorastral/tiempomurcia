#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera las efemérides "Olas de calor" y "Olas de frío" a partir de murcia_data.js:

  - informe_olas_calor.html  -> episodios de calor por estación
  - informe_olas_frio.html   -> episodios de frío por estación
  - efemerides.js            -> registro para el menú Efemérides de la app

Criterios (adaptados de la metodología de AEMET, para una sola estación):
  · Ola de CALOR: >= 3 días consecutivos con la MÁXIMA por encima del percentil 95
    de las máximas diarias de julio y agosto del periodo de referencia 1984-2013.
  · Ola de FRÍO:  >= 3 días consecutivos con la MÍNIMA por debajo del percentil 5
    de las mínimas diarias de enero y febrero del mismo periodo.
  · Si el episodio se interrumpe un solo día, se considera la misma ola.

Uso:  python generar_efemerides.py    (tras descargar los datos)
"""

import json
import os
import re
import sys
from datetime import date, datetime

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "murcia_data.js")
EFEMERIDES = os.path.join(AQUI, "efemerides.js")

REF_INI, REF_FIN = 1984, 2013   # periodo de referencia para los percentiles

TIPOS = [
    {"clave": "calor", "emoji": "🔥", "titulo": "Olas de calor",
     "idx": 3, "var": "máxima", "var_plural": "máximas", "meses_ref": (7, 8),
     "pctl": 0.95, "sobre": True, "meses_txt": "julio y agosto",
     "umbral_txt": "por encima del percentil 95",
     "pico_txt": "Las 5 de pico más alto", "archivo": "informe_olas_calor.html"},
    {"clave": "frio", "emoji": "🧊", "titulo": "Olas de frío",
     "idx": 2, "var": "mínima", "var_plural": "mínimas", "meses_ref": (1, 2),
     "pctl": 0.05, "sobre": False, "meses_txt": "enero y febrero",
     "umbral_txt": "por debajo del percentil 5",
     "pico_txt": "Las 5 de pico más bajo", "archivo": "informe_olas_frio.html"},
]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_es(s):
    d = datetime.strptime(s, "%Y-%m-%d")
    return f"{d.day} de {MESES[d.month-1]} de {d.year}"


def pctl(valores, p):
    """Percentil con interpolación lineal (como numpy 'linear')."""
    v = sorted(valores)
    if not v:
        return None
    k = p * (len(v) - 1)
    i = int(k)
    if i + 1 >= len(v):
        return v[-1]
    return v[i] + (v[i + 1] - v[i]) * (k - i)


def detectar_olas(filas, umbral, idx, sobre):
    """Rachas de días CONSECUTIVOS de calendario que cumplen el criterio; se unen
    las separadas por un solo día y se exigen >=3 días seguidos cumpliéndolo."""
    rachas = []  # [ini(date), fin(date), [(fecha, valor), ...]]
    prev_fecha = None
    for r in filas:
        f = r[0]
        v = r[idx] if len(r) > idx else None
        d = date.fromisoformat(f)
        cumple = v is not None and (v > umbral if sobre else v < umbral)
        if cumple:
            if rachas and prev_fecha is not None and (d - prev_fecha).days == 1 and rachas[-1][1] == prev_fecha:
                rachas[-1][1] = d
                rachas[-1][2].append((f, v))
            else:
                rachas.append([d, d, [(f, v)]])
        prev_fecha = d

    # Unir rachas separadas por exactamente 1 día ("si se interrumpe un solo día, es la misma ola")
    unidas = []
    for rc in rachas:
        if unidas and (rc[0] - unidas[-1][1]).days == 2:
            unidas[-1][1] = rc[1]
            unidas[-1][2].extend(rc[2])
        else:
            unidas.append(rc)

    # Ola = episodio que contiene al menos 3 días consecutivos cumpliendo el criterio
    olas = []
    for ini, fin, dias in unidas:
        consec = mejor = 1
        for a, b in zip(dias, dias[1:]):
            consec = consec + 1 if (date.fromisoformat(b[0]) - date.fromisoformat(a[0])).days == 1 else 1
            mejor = max(mejor, consec)
        if mejor < 3:
            continue
        pico = (max if sobre else min)(dias, key=lambda x: x[1])
        olas.append({
            "ini": ini.isoformat(), "fin": fin.isoformat(),
            "duracion": (fin - ini).days + 1,
            "dias_sobre": len(dias),
            "pico": pico[1], "fecha_pico": pico[0],
            "media": round(sum(x[1] for x in dias) / len(dias), 1),
        })
    return olas


def informe(tipo, datos, provisional):
    """Construye el HTML de un tipo (calor/frío). Devuelve (resumen_menu, n_total)."""
    secciones, resumen_menu, total = [], [], 0
    col_pico = "Pico" if tipo["sobre"] else "Mínimo"
    for st in datos["stations"]:
        filas = datos["data"][str(st["code"])]
        idx = tipo["idx"]
        ref = [r[idx] for r in filas
               if len(r) > idx and r[idx] is not None
               and REF_INI <= int(r[0][:4]) <= REF_FIN and int(r[0][5:7]) in tipo["meses_ref"]]
        if len(ref) < 500:
            print(f"  {st['short']} ({tipo['clave']}): referencia insuficiente, se omite.")
            continue
        umbral = round(pctl(ref, tipo["pctl"]), 1)
        olas = detectar_olas(filas, umbral, idx, tipo["sobre"])
        total += len(olas)
        signo = ">" if tipo["sobre"] else "<"
        print(f"  {st['short']} ({tipo['clave']}): umbral {signo} {umbral} °C · {len(olas)} olas")

        top_dur = sorted(olas, key=lambda o: (-o["dias_sobre"], -abs(o["media"] - umbral)))[:5]
        top_int = sorted(olas, key=lambda o: -o["pico"] if tipo["sobre"] else o["pico"])[:5]
        decadas = {}
        for o in olas:
            d = decadas.setdefault(f"{o['ini'][:3]}0s", {"n": 0, "dias": 0})
            d["n"] += 1
            d["dias"] += o["dias_sobre"]

        fila_ola = lambda o: (
            f"<tr><td>{fecha_es(o['ini'])} → {fecha_es(o['fin'])}</td>"
            f"<td>{o['duracion']}</td><td>{o['dias_sobre']}</td>"
            f"<td><b>{o['pico']:.1f} °C</b> ({fecha_es(o['fecha_pico'])})</td>"
            f"<td>{o['media']:.1f} °C</td></tr>")
        cab = (f"<thead><tr><th>Episodio</th><th>Duración (días)</th><th>Días de criterio</th>"
               f"<th>{col_pico}</th><th>Media ({tipo['var']})</th></tr></thead>")

        secciones.append(f"""
<section>
  <h2><span class="dot" style="background:{st['color']}"></span> {st['name'].replace(' (ERA5, prov.)','')} — {len(olas)} {tipo['titulo'].lower()}</h2>
  <p class="meta">Umbral: {tipo['var_plural']} {signo} <b>{umbral} °C</b> ({tipo['umbral_txt']} de las {tipo['var_plural']} de {tipo['meses_txt']} {REF_INI}–{REF_FIN}).
     Serie analizada: {filas[0][0][:4]}–{filas[-1][0][:4]}.</p>
  <h3>🏆 Las 5 más largas (por días cumpliendo el criterio)</h3>
  <table>{cab}<tbody>{''.join(fila_ola(o) for o in top_dur)}</tbody></table>
  <h3>{tipo['emoji']} {tipo['pico_txt']}</h3>
  <table>{cab}<tbody>{''.join(fila_ola(o) for o in top_int)}</tbody></table>
  <h3>📅 Por décadas</h3>
  <table class="mini"><thead><tr><th>Década</th><th>Olas</th><th>Días de ola</th></tr></thead>
  <tbody>{''.join(f"<tr><td>{d}</td><td>{v['n']}</td><td>{v['dias']}</td></tr>" for d, v in sorted(decadas.items()))}</tbody></table>
  <h3>📜 Todas las olas (recientes primero)</h3>
  <table>{cab}<tbody>{''.join(fila_ola(o) for o in sorted(olas, key=lambda o: o['ini'], reverse=True))}</tbody></table>
</section>""")
        resumen_menu.append(f"{st['short']}: {len(olas)}")

    aviso = ("<div class='aviso'>⚠️ Datos provisionales del reanálisis ERA5 (Open-Meteo): los picos pueden "
             "diferir 1–3 °C de la medida real de la estación. El informe se regenerará automáticamente "
             "cuando entren los datos oficiales de AEMET.</div>") if provisional else ""

    criterio = (f"episodio de al menos <b>3 días consecutivos</b> con temperatura {tipo['var']} "
                f"{tipo['umbral_txt']} de las {tipo['var_plural']} diarias de {tipo['meses_txt']} del periodo "
                f"de referencia <b>{REF_INI}–{REF_FIN}</b>. Si el episodio se interrumpe un solo día, se "
                "considera la misma ola. «Días de criterio» cuenta solo los días que lo cumplen; "
                "«duración» abarca todo el episodio.")

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{tipo['titulo']} · Murcia y Caravaca</title>
<style>
  body{{font-family:"Inter","Segoe UI",system-ui,sans-serif;margin:0;padding:28px 34px;background:#fbfbfb;color:#1a1a1a;line-height:1.55;font-size:14.5px;}}
  h1{{font-size:22px;margin:0 0 4px;}} .sub{{color:#6b6b6b;font-size:13px;margin-bottom:18px;}}
  h2{{font-size:17px;margin:30px 0 4px;display:flex;align-items:center;gap:8px;}}
  h3{{font-size:13px;text-transform:uppercase;letter-spacing:.8px;color:{'#e8632a' if tipo['sobre'] else '#1f6feb'};margin:20px 0 6px;}}
  .dot{{width:14px;height:14px;border-radius:50%;display:inline-block;box-shadow:0 0 0 1px #ddd;}}
  .meta{{color:#6b6b6b;font-size:12.5px;margin:2px 0 10px;}}
  .aviso{{background:#fff4ee;border:1.5px solid #e8632a;border-radius:10px;padding:10px 14px;font-size:13px;margin:14px 0;}}
  table{{border-collapse:collapse;width:100%;font-size:12.5px;margin-bottom:8px;}}
  th,td{{border:1px solid #e4e4e4;padding:5px 9px;text-align:left;}}
  th{{background:#f5f0ec;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px;}}
  tr:nth-child(even) td{{background:#fafafa;}}
  .mini{{max-width:420px;}}
  .criterio{{background:#f5f0ec;border-radius:10px;padding:12px 16px;font-size:13px;}}
</style></head><body>
<h1>{tipo['emoji']} {tipo['titulo']}</h1>
<div class="sub">Murcia y Caravaca de la Cruz · generado el {fecha_es(date.today().isoformat())} a partir de los datos cargados en la aplicación</div>
{aviso}
<div class="criterio"><b>Criterio</b> (adaptado de la metodología de AEMET): {criterio}</div>
{''.join(secciones)}
</body></html>"""
    open(os.path.join(AQUI, tipo["archivo"]), "w", encoding="utf-8").write(html)
    return resumen_menu


def main():
    if not os.path.exists(ENTRADA):
        sys.exit("No existe murcia_data.js: descarga antes los datos.")
    txt = open(ENTRADA, encoding="utf-8").read()
    m = re.search(r"=\s*(\{.*\})\s*;?\s*$", txt, re.S)
    datos = json.loads(m.group(1))
    provisional = datos.get("source") != "aemet"

    entradas = []
    for tipo in TIPOS:
        print(f"— {tipo['titulo']} —")
        resumen = informe(tipo, datos, provisional)
        entradas.append({
            "titulo": f"{tipo['emoji']} {tipo['titulo']} ({' · '.join(resumen)})",
            "archivo": tipo["archivo"],
        })

    with open(EFEMERIDES, "w", encoding="utf-8") as f:
        f.write("// Generado por generar_efemerides.py — se rehace en cada actualización de datos\n")
        f.write("window.EFEMERIDES = " + json.dumps(entradas, ensure_ascii=False, indent=2) + ";\n")
    print(f"✅ Informes y {os.path.basename(EFEMERIDES)} generados.")


if __name__ == "__main__":
    main()
