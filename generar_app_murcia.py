#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera Murcia_app_explorador.html a partir de Albertville_app_explorador.html.

Los datos NO van embebidos: la app de Murcia los carga del archivo hermano
murcia_data.js (lo produce descargar_aemet_murcia.py). Así este generador se
puede volver a ejecutar si la app de Albertville evoluciona.

Uso:  python generar_app_murcia.py
"""

import os
import re
import sys

# Consolas Windows con cp1252: no reventar por emojis/flechas en los print
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(AQUI, "Albertville_app_explorador.html")
DESTINO = os.path.join(AQUI, "Murcia_app_explorador.html")

with open(ORIGEN, encoding="utf-8") as f:
    txt = f.read()

errores = []

def sub(old, new, nombre):
    global txt
    n = txt.count(old)
    if n != 1:
        errores.append(f"[{nombre}] esperaba 1 aparición, hay {n}")
        return
    txt = txt.replace(old, new)

def sub_re(patron, new, nombre, flags=re.S):
    global txt
    m = re.findall(patron, txt, flags)
    if len(m) != 1:
        errores.append(f"[{nombre}] regex: esperaba 1 aparición, hay {len(m)}")
        return
    txt = re.sub(patron, new, txt, count=1, flags=flags)

# ---------- 1. Cabecera del documento ----------
sub("<title>Albertville · Explorador de datos meteorológicos</title>",
    "<title>Murcia y Caravaca · Explorador de datos meteorológicos</title>", "title")

sub('<script src="tournon_live.js"></script>  <!-- datos actualizados de Tournon (lo genera actualizar_tournon.bat); persiste entre versiones -->\n'
    '<script src="ugine_live.js"></script>  <!-- datos actualizados de Ugine 539m; mismo actualizador -->',
    '<script src="murcia_data.js"></script>  <!-- datos AEMET de Murcia y Caravaca (los genera actualizar_murcia.bat / descargar_aemet_murcia.py) -->',
    "scripts live")

sub('<h1>📊 <span data-fr="Albertville · Explorateur de données météorologiques">Albertville · Explorador de datos meteorológicos</span></h1>',
    '<h1>📊 <span data-fr="Murcie et Caravaca · Explorateur de données météorologiques">Murcia y Caravaca · Explorador de datos meteorológicos</span></h1>',
    "h1")

sub('<div class="sub"><span data-fr="5 stations · 1948-2026 · 54 242 jours de données">5 estaciones · 1948-2026 · 54.242 días de datos</span> <span style="opacity:.6;font-size:11px;margin-left:8px;">· v4.04</span></div>',
    '<div class="sub"><span id="hdr-sub">AEMET OpenData · Murcia (7178I) y Caravaca de la Cruz (7119B)</span> <span style="opacity:.6;font-size:11px;margin-left:8px;">· v1.00 Murcia</span></div>',
    "subtítulo")

sub('<button id="upd-toggle" class="ctrl-btn" title="Actualizar datos de Tournon">',
    '<button id="upd-toggle" class="ctrl-btn" title="Actualizar datos de AEMET">', "botón actualizar")

# ---------- 2. Sidebar ----------
sub('    <h3 style="margin-top:14px;">🔗 <span data-fr="Station combinée">Estación combinada</span></h3>\n'
    '    <div class="st-list" id="st-list-combined"></div>\n', '', "sección combinada")

sub('<button class="pill" data-vargroup="snow">❄️ <span data-fr="Neige">Nieve</span></button>',
    '<button class="pill" data-vargroup="sol">☀️ <span data-fr="Soleil">Sol</span></button>', "pill nieve→sol")

sub('<input type="number" id="range-from" min="1948" max="2026" value="2000">',
    '<input type="number" id="range-from" min="1984" max="2030" value="2000">', "range-from")
sub('<input type="number" id="range-to" min="1948" max="2026" value="2026">',
    '<input type="number" id="range-to" min="1984" max="2030" value="2026">', "range-to")

# Series climatológicas anteriores a los datos AEMET (1984)
for ref, nombre in [
    ('          <button data-ref="1961-1990">1961–1990</button>\n', "ref 1961-1990"),
    ('          <button data-ref="1971-2000">1971–2000</button>\n', "ref 1971-2000"),
    ('          <button data-ref="1950-1959"><span data-fr="Années 50">Años 50</span></button>\n', "ref años 50"),
    ('          <button data-ref="1960-1969"><span data-fr="Années 60">Años 60</span></button>\n', "ref años 60"),
    ('          <button data-ref="1970-1979"><span data-fr="Années 70">Años 70</span></button>\n', "ref años 70"),
]:
    sub(ref, '', nombre)

sub('<h3>🔄 <span data-fr="Mettre à jour les données de Tournon">Actualizar datos de Tournon</span></h3>',
    '<h3>🔄 <span data-fr="Mettre à jour les données AEMET">Actualizar datos de AEMET</span></h3>', "modal actualizar h3")

# ---------- 3. Estado inicial y variables ----------
sub('let curStations = new Set([999999]); // arranque: estación combinada Albertville',
    'let curStations = new Set([7178]); // arranque: Murcia', "curStations inicial")

sub("  'fxi': {label:'Racha instantánea (km/h)', label_fr:'Rafale instantanée (km/h)', color:'#00bfa5', unit:'km/h', idx:15, type:'max'},\n};",
    "  'fxi': {label:'Racha instantánea (km/h)', label_fr:'Rafale instantanée (km/h)', color:'#00bfa5', unit:'km/h', idx:15, type:'max'},\n"
    "  'sol': {label:'Horas de sol (h)', label_fr:\"Heures d'ensoleillement (h)\", color:'#f9a825', unit:'h', idx:16, type:'mean'},\n};",
    "VAR_INFO sol")

# ---------- 4. Datos: de embebidos a externos ----------
sub_re(r'const EMBEDDED_DATA = \{"fields".*',
       "const EMBEDDED_DATA = (typeof window !== 'undefined' && window.MURCIA_DATA) ? window.MURCIA_DATA : "
       '{"fields":["date","rr","tn","tx","tm","ffm","fxy","qcflags","fxy_ms","um","ux","un","res12","res13","tntxm","fxi","sol"],"stations":[],"data":{}};',
       "EMBEDDED_DATA", flags=0)

sub_re(r'/\* === TOURNON_LIVE.*?window\.UGINE_LIVE\);\n\}\n', '', "bloques live")

# ---------- 5. QC nivel 3 (contraste con Météo-France): no aplica ----------
sub_re(r'// ========= QC NIVEL 3.*?\n\};\n\n', '', "const QC_EXT")
sub_re(r" \+\n\s*`<div class=\"qc-l3\">.*?`</div>`;", ";", "panel QC nivel 3")

# ---------- 6. QC: contar y validar horas de sol ----------
sub("      for(const k of [1,2,3,4,5,6,9,10,11,12,13,15]) if(r[k]!=null) q.vals++;",
    "      for(const k of [1,2,3,4,5,6,9,10,11,12,13,15,16]) if(r[k]!=null) q.vals++;", "QC contar sol")
sub("      if(r[15]!=null && (r[15]<0||r[15]>300)) excl(r,15,'FXI','F_FISICO','Fuera de límites físicos [0,300] km/h');",
    "      if(r[15]!=null && (r[15]<0||r[15]>300)) excl(r,15,'FXI','F_FISICO','Fuera de límites físicos [0,300] km/h');\n"
    "      if(r[16]!=null && (r[16]<0||r[16]>16)) excl(r,16,'SOL','F_FISICO','Fuera de límites físicos [0,16] h');",
    "QC límite sol")

# ---------- 7. Sin estación combinada (Murcia y Caravaca están a 60 km) ----------
sub_re(r'// Estación combinada "Albertville".*?\n\}\)\(\);',
       '// Sin estación combinada en esta versión: Murcia y Caravaca son series independientes.\n'
       'const ALB_CODE = 999999;\n'
       '// Métrica derivada TNTXM = (TN+TX)/2 (la "media tradicional"; la TM oficial de AEMET\n'
       '// es la media de las 24 horarias). Calculada para todas las estaciones.\n'
       'Object.keys(DB.data).forEach(c => DB.data[c].forEach(r => {\n'
       '  if(r[2] != null && r[3] != null) r[14] = Math.round((r[2] + r[3]) * 5) / 10;\n'
       '}));',
       "estación combinada")

# ---------- 8. Cabecera dinámica + aviso si faltan datos ----------
sub("window.addEventListener('DOMContentLoaded', () => {\n"
    "  document.getElementById('loading').classList.add('hidden');\n",
    "window.addEventListener('DOMContentLoaded', () => {\n"
    "  document.getElementById('loading').classList.add('hidden');\n"
    "  // Cabecera dinámica y aviso si aún no hay datos descargados\n"
    "  (function(){\n"
    "    const el = document.getElementById('hdr-sub');\n"
    "    if(el && DB.stations.length){\n"
    "      let days = 0, minY = 9999, maxY = 0;\n"
    "      DB.stations.forEach(st => { const rows = DB.data[st.code]||[]; days += rows.length;\n"
    "        if(rows.length){ minY = Math.min(minY, +rows[0][0].slice(0,4)); maxY = Math.max(maxY, +rows[rows.length-1][0].slice(0,4)); } });\n"
    "      const fuente = DB.source === 'open-meteo' ? '⚠ Open-Meteo ERA5 (provisional, no oficial)' : 'AEMET OpenData';\n"
    "      el.textContent = DB.stations.length + (DB.stations.length===1?' estación · ':' estaciones · ') + minY + '-' + maxY + ' · ' + days.toLocaleString('es-ES') + ' días de datos · ' + fuente;\n"
    "    }\n"
    "    if(!DB.stations.length){\n"
    "      const main = document.querySelector('main');\n"
    "      if(main){\n"
    "        const d = document.createElement('div');\n"
    "        d.style.cssText = 'background:#fff4ee;border:2px solid #e8632a;border-radius:12px;padding:18px 22px;margin-bottom:16px;font-size:14px;line-height:1.7;color:#1a1a1a;';\n"
    "        d.innerHTML = '<b>⚠️ Aún no hay datos.</b> Pega tu API Key de AEMET en <b>aemet_api_key.txt</b> y haz doble clic en <b>actualizar_murcia.bat</b> (junto a este archivo). Cuando termine, recarga esta página.';\n"
    "        main.insertBefore(d, main.firstChild);\n"
    "      }\n"
    "    }\n"
    "  })();\n",
    "cabecera dinámica")

# ---------- 9. Arranque: Murcia, mes en curso ----------
sub("  bootTournonMesActual();   // arranque fijo: Tournon · mes en curso · temperatura media",
    "  bootMurciaMesActual();   // arranque fijo: Murcia · mes en curso · temperatura media", "llamada boot")
sub("// Arranque: estación de Tournon, mes actual, gráfica de temperatura media\n"
    "function bootTournonMesActual(){\n"
    "  const T = 73297003;",
    "// Arranque: estación de Murcia, mes actual, gráfica de temperatura media\n"
    "function bootMurciaMesActual(){\n"
    "  const T = 7178;", "función boot")
sub("  // Si el mes en curso aún no tiene datos de Tournon, usar el último mes disponible",
    "  // Si el mes en curso aún no tiene datos de Murcia, usar el último mes disponible", "comentario boot")

# ---------- 10. Grupos de variables: sol en vez de nieve ----------
sub("const VAR_GROUPS = { temp:['tntxm','tx','tn','tm'], rain:['rr'], wind:['ffm','fxy','fxi'], hum:['um','ux','un'], snow:['hneigef','neigetotx'] };",
    "const VAR_GROUPS = { temp:['tntxm','tx','tn','tm'], rain:['rr'], wind:['ffm','fxy'], hum:['um','ux','un'], sol:['sol'] };",
    "VAR_GROUPS")
sub("  fxy:{es:'Racha máx 10-min (km/h)',fr:'Rafale max 10-min (km/h)'},",
    "  fxy:{es:'Racha máxima (km/h)',fr:'Rafale maximale (km/h)'},", "label fxy")
sub("  neigetotx:{es:'Espesor máx (cm)',fr:'Épaisseur max (cm)'},\n};",
    "  neigetotx:{es:'Espesor máx (cm)',fr:'Épaisseur max (cm)'},\n"
    "  sol:{es:'Horas de sol (h)',fr:\"Heures d'ensoleillement (h)\"},\n};", "METRIC_LABELS sol")
sub("function varGroupOf(v){ return v==='rr' ? 'rain' : (v==='ffm'||v==='fxy'||v==='fxi') ? 'wind' : (v==='um'||v==='ux'||v==='un') ? 'hum' : (v==='hneigef'||v==='neigetotx') ? 'snow' : 'temp'; }",
    "function varGroupOf(v){ return v==='rr' ? 'rain' : (v==='ffm'||v==='fxy'||v==='fxi') ? 'wind' : (v==='um'||v==='ux'||v==='un') ? 'hum' : v==='sol' ? 'sol' : 'temp'; }",
    "varGroupOf")

# ---------- 11. Modal "Actualizar": instrucciones AEMET ----------
sub_re(r"document\.getElementById\('upd-body'\)\.innerHTML = L\(\).*?doble clic\.</p>`;",
       "document.getElementById('upd-body').innerHTML = L()\n"
       "      ? `<p>Pour récupérer les derniers jours depuis <b>AEMET OpenData</b> :</p>\n"
       "         <ol style=\"line-height:1.9\">\n"
       "           <li>Vérifie que ta clé API est dans <b>aemet_api_key.txt</b>.</li>\n"
       "           <li>Double-clic sur <b>actualizar_murcia.bat</b> (à côté de cette application).</li>\n"
       "           <li>Quand il a fini, l'application s'ouvre toute seule avec les données à jour.</li>\n"
       "         </ol>\n"
       "         <p style=\"color:var(--mut);font-size:13px\">Note : pour des raisons de sécurité du navigateur, un fichier local ne peut pas télécharger lui-même depuis Internet. Le .bat s'en charge.</p>`\n"
       "      : `<p>Para traer los días más recientes desde <b>AEMET OpenData</b>:</p>\n"
       "         <ol style=\"line-height:1.9\">\n"
       "           <li>Comprueba que tu API Key está en <b>aemet_api_key.txt</b> (junto a esta aplicación).</li>\n"
       "           <li>Haz doble clic en <b>actualizar_murcia.bat</b>.</li>\n"
       "           <li>Cuando termine, la aplicación se abre sola con los datos al día.</li>\n"
       "         </ol>\n"
       "         <p style=\"color:var(--mut);font-size:13px\">Nota: por seguridad del navegador, un archivo local no puede descargar de Internet por sí mismo. El .bat lo hace por ti en un doble clic.</p>`;",
       "modal actualizar")

# ---------- 12. Texto de ayuda de la tabla climatológica ----------
sub("        ${L?'Pour la climatologie historique :':'Para climatología histórica:'}<br>\n"
    "        • ${L?'sélectionne la station combinée':'selecciona la estación combinada'} <b>«Albertville»</b> (${L?'à gauche, 1948–2026':'a la izquierda, 1948–2026'}), ${L?'ou':'o'} <b>JO</b> / <b>Gilly</b>.<br>\n"
    "        • ${L?'ou choisis une période récente':'o elige un periodo reciente'}: <b>2000–${L?'auj.':'act.'}</b>, <b>2020s</b>.",
    "        ${L?'Pour la climatologie historique :':'Para climatología histórica:'}<br>\n"
    "        • ${L?'choisis une période couverte par la série':'elige un periodo cubierto por la serie'} (${L?'depuis':'desde'} 1984): <b>1991–2020</b>, <b>2000–${L?'auj.':'act.'}</b>, <b>2010s</b>, <b>2020s</b>.",
    "ayuda tabla")

# ---------- 12b. Comparar años: color FIJO por año ----------
# Antes el color dependía de la posición en la lista ordenada: al añadir un año
# anterior (p.ej. 1989 con 2025 ya puesto), todos los demás cambiaban de color.
sub("let chartInstance = null;\nlet lbChartInstance = null;",
    "let chartInstance = null;\nlet lbChartInstance = null;\n"
    "// Colores fijos por año en el modo comparar: cada año conserva su color aunque\n"
    "// se añadan o quiten otros. El color se libera al deseleccionar el año.\n"
    "const YEAR_PALETTE = ['#ff3b30','#00c7ff','#ffd60a','#9b59b6','#2ecc71','#ff8c00','#ff66cc','#1f6feb','#a8e10c','#8b4513','#00e5b0','#e6194b','#5856d6','#ffa3a3','#0a84ff','#d4ff00','#c0392b','#7fdbff','#f39c12','#e0e0e0'];\n"
    "const YEAR_COLOR_MAP = new Map();\n"
    "function yearColor(y){\n"
    "  y = +y;\n"
    "  if(YEAR_COLOR_MAP.has(y)) return YEAR_COLOR_MAP.get(y);\n"
    "  const used = new Set(YEAR_COLOR_MAP.values());\n"
    "  let col = YEAR_PALETTE.find(c => !used.has(c));\n"
    "  if(!col) col = YEAR_PALETTE[YEAR_COLOR_MAP.size % YEAR_PALETTE.length];\n"
    "  YEAR_COLOR_MAP.set(y, col);\n"
    "  return col;\n"
    "}\n"
    "function pruneYearColors(){\n"
    "  for(const y of [...YEAR_COLOR_MAP.keys()]) if(!curCompareYears.has(y)) YEAR_COLOR_MAP.delete(y);\n"
    "}",
    "helper yearColor")
sub("  // Quitar de curCompareYears años no disponibles\n"
    "  for(const y of [...curCompareYears]) if(!yrs.has(y)) curCompareYears.delete(y);",
    "  // Quitar de curCompareYears años no disponibles\n"
    "  for(const y of [...curCompareYears]) if(!yrs.has(y)) curCompareYears.delete(y);\n"
    "  pruneYearColors();",
    "prune colores")
sub("      backgroundColor: singleStation ? yearsArr.map((y,yi)=>yearPalette[yi%yearPalette.length]+'cc') : stColor+'cc',\n"
    "      borderColor:     singleStation ? yearsArr.map((y,yi)=>yearPalette[yi%yearPalette.length])      : stColor,",
    "      backgroundColor: singleStation ? yearsArr.map(y=>yearColor(y)+'cc') : stColor+'cc',\n"
    "      borderColor:     singleStation ? yearsArr.map(y=>yearColor(y))      : stColor,",
    "color fijo: barras total")
sub("      const col = single ? null : yearPalette[yi % yearPalette.length];",
    "      const col = single ? null : yearColor(y);",
    "color fijo: climograma")
sub("      const color = stations.length > 1 ? (st.color === '#FFE08A' ? '#c79900' : st.color) : yearPalette[yi % yearPalette.length];",
    "      const color = stations.length > 1 ? (st.color === '#FFE08A' ? '#c79900' : st.color) : yearColor(y);",
    "color fijo: meses del año")
sub("      if(singleStation){\n        color = yearPalette[yi % yearPalette.length];",
    "      if(singleStation){\n        color = yearColor(y);",
    "color fijo: mensual por días")

# ---------- 13. Nombres de archivo exportados y localStorage ----------
sub("a.download = `albertville_${[...curStations].join('-')}_${curVar}_${curChart}.png`;",
    "a.download = `murcia_${[...curStations].join('-')}_${curVar}_${curChart}.png`;", "nombre png")
sub("_csvDescargar(csv, 'albertville_tabla_anual.csv');",
    "_csvDescargar(csv, 'murcia_tabla_anual.csv');", "nombre csv tabla")
sub("_csvDescargar(lines.join('\\r\\n'), 'albertville_datos_diarios.csv');",
    "_csvDescargar(lines.join('\\r\\n'), 'murcia_datos_diarios.csv');", "nombre csv diario")
sub("const key = 'alb_sec_' + h.dataset.sec;", "const key = 'mur_sec_' + h.dataset.sec;", "ls secciones")
sub("localStorage.setItem('alb_app_state', JSON.stringify(st));",
    "localStorage.setItem('mur_app_state', JSON.stringify(st));", "ls guardar")
sub("const raw = localStorage.getItem('alb_app_state');",
    "const raw = localStorage.getItem('mur_app_state');", "ls leer")

# ---------- Resultado ----------
if errores:
    print("❌ El generador NO ha escrito nada. Parches que no encajan:")
    for e in errores:
        print("   -", e)
    sys.exit(1)

with open(DESTINO, "w", encoding="utf-8") as f:
    f.write(txt)
print(f"✅ Generado {os.path.basename(DESTINO)} ({len(txt)/1024:.0f} KB)")
