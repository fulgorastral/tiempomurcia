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
    "      const dmy = s => s ? s.slice(8,10)+'/'+s.slice(5,7)+'/'+s.slice(0,4) : '';\n"
    "      let ultimo = '';\n"
    "      DB.stations.forEach(st => { const rows = DB.data[st.code]||[];\n"
    "        if(rows.length && rows[rows.length-1][0] > ultimo) ultimo = rows[rows.length-1][0]; });\n"
    "      el.textContent = DB.stations.length + (DB.stations.length===1?' estación · ':' estaciones · ') + minY + '-' + maxY + ' · ' + days.toLocaleString('es-ES') + ' días de datos · ' + fuente\n"
    "        + (ultimo ? ' · datos hasta el ' + dmy(ultimo) : '')\n"
    "        + (DB.generado ? ' · actualizado el ' + dmy(DB.generado) : '');\n"
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

# ---------- 14. Comparar años en móvil + tooltip en HTML ----------
sub("  .chart-canvas-wrap{position:relative;height:440px;}",
    "  .chart-canvas-wrap{position:relative;height:440px;}\n  /* Tooltip del gráfico en HTML: el de canvas no permite jerarquía tipográfica ni color */\n  .cjs-tt{position:absolute;pointer-events:none;z-index:20;opacity:0;transition:opacity .12s;\n    background:var(--card);color:var(--ink);border:1px solid var(--border);border-radius:12px;\n    box-shadow:0 8px 28px rgba(0,0,0,.18);padding:12px 14px;min-width:200px;max-width:320px;\n    font-size:12.5px;line-height:1.45;}\n  .cjs-tt .tt-serie-val{justify-content:flex-start;}\n  .cjs-tt .tt-serie-val .tt-serie-num{margin-left:auto;font-variant-numeric:tabular-nums;\n    white-space:nowrap;padding-left:14px;}\n  .cjs-tt .tt-cap{font-size:10.5px;color:var(--mut);margin:-3px 0 4px 22px;\n    font-variant-numeric:tabular-nums;}\n  .cjs-tt .tt-date{font-size:11px;font-weight:700;letter-spacing:.5px;color:var(--mut);\n    text-transform:uppercase;margin-bottom:9px;}\n  .cjs-tt .tt-serie{display:flex;align-items:center;gap:7px;font-weight:700;margin:11px 0 6px;}\n  .cjs-tt .tt-serie:first-of-type{margin-top:0;}\n  .cjs-tt .tt-key{width:15px;height:3px;border-radius:2px;flex:none;}\n  .cjs-tt .tt-hero{font-size:24px;font-weight:800;letter-spacing:-.6px;line-height:1.1;\n    font-variant-numeric:tabular-nums;}\n  .cjs-tt .tt-hero-lbl{font-size:11px;color:var(--mut);margin-bottom:8px;}\n  .cjs-tt .tt-badge{display:inline-block;font-size:11.5px;font-weight:700;padding:2px 9px;\n    border-radius:999px;margin-bottom:9px;}\n  .cjs-tt .tt-badge.up{background:#fdecea;color:#b3261e;}\n  .cjs-tt .tt-badge.down{background:#e8f1fb;color:#12518f;}\n  .cjs-tt .tt-row{display:flex;justify-content:space-between;gap:16px;font-size:12px;}\n  .cjs-tt .tt-row span:first-child{color:var(--mut);}\n  .cjs-tt .tt-row span:last-child{font-weight:700;font-variant-numeric:tabular-nums;}\n  .cjs-tt .tt-plain{font-size:12px;}\n  .cjs-tt .tt-bar{position:relative;height:7px;border-radius:4px;background:var(--hover);\n    border:1px solid var(--border);margin:8px 0 3px;}\n  .cjs-tt .tt-bar i{position:absolute;top:0;height:100%;border-radius:4px;}\n  .cjs-tt .tt-bar b{position:absolute;top:-4px;width:2px;height:13px;border-radius:1px;background:#e0a800;}\n  .cjs-tt .tt-ends{display:flex;justify-content:space-between;font-size:10.5px;color:var(--mut);\n    font-variant-numeric:tabular-nums;margin-bottom:7px;}\n  html[data-theme=\"dark\"] .cjs-tt{box-shadow:0 8px 28px rgba(0,0,0,.55);}\n  html[data-theme=\"dark\"] .cjs-tt .tt-badge.up{background:#3a1512;color:#ff9d92;}\n  html[data-theme=\"dark\"] .cjs-tt .tt-badge.down{background:#0f2438;color:#8fc2f5;}",
    "css: tooltip HTML")
sub("  .quick-btn:hover{border-style:solid;color:var(--warm);border-color:var(--warm);}",
    "  .quick-btn:hover{border-style:solid;color:var(--warm);border-color:var(--warm);}\n  /* Modo comparar: imprescindible en móvil, donde no hay Ctrl+clic */\n  .quick-btn.on{border-style:solid;background:var(--warm);border-color:var(--warm);color:#fff;}",
    "css: botón modo comparar")
sub("          <small><span data-fr=\"clic = 1 an · Ctrl+clic = plusieurs\">clic = 1 año · Ctrl+clic = comparar varios</span></small></div>",
    "          <small><span data-fr=\"1 clic = 1 an · Ctrl+clic ou «➕ Plusieurs» = comparer\">1 clic = 1 año · Ctrl+clic o «➕ Varios» = comparar</span></small></div>",
    "texto ayuda comparar")
sub("        <div class=\"year-shortcuts\">",
    "        <div class=\"year-shortcuts\">\n          <button class=\"quick-btn\" data-quick=\"cmp\" id=\"cmp-toggle\" title=\"Ir tocando años para compararlos (en móvil no hay Ctrl+clic)\"><span data-fr=\"➕ Plusieurs\">➕ Varios</span></button>",
    "botón ➕ Varios")
sub("let curCompareYears = new Set();",
    "let curCompareYears = new Set();\nlet cmpMode = false;   // modo comparar: cada toque añade/quita un año (alternativa táctil a Ctrl+clic)\n\n// ---- Tooltip del gráfico en HTML --------------------------------------------\n// El tooltip de Chart.js se dibuja en canvas: no admite negritas, color ni\n// columnas alineadas. Lo sacamos a HTML para poder jerarquizar la información.\n// El callback label() marca las líneas con TT_SEP; las que no llevan marca se\n// pintan tal cual, así los gráficos que no la usan siguen funcionando igual.\nconst TT_SEP = '\\x1f';\nfunction renderChartTooltip(ctx){\n  const {chart, tooltip} = ctx;\n  const wrap = chart.canvas.parentNode;\n  let el = wrap.querySelector('.cjs-tt');\n  if(!el){ el = document.createElement('div'); el.className = 'cjs-tt'; wrap.appendChild(el); }\n  if(tooltip.opacity === 0){ el.style.opacity = 0; return; }\n  try{\n    const frag = document.createDocumentFragment();\n    const add = (cls, txt) => { const d = document.createElement('div'); d.className = cls;\n      if(txt != null) d.textContent = txt; frag.appendChild(d); return d; };\n    const par = (padre, txt, peso) => { const s = document.createElement('span');\n      s.textContent = txt; if(peso) s.style.fontWeight = peso; padre.appendChild(s); return s; };\n    (tooltip.title || []).forEach(t => add('tt-date', t));\n    (tooltip.body || []).forEach((b, i) => {\n      const col = (tooltip.labelColors || [])[i] || {};\n      (b.lines || []).forEach((linea, j) => {\n        const s = String(linea);\n        // Primera línea sin marca = nombre de la serie, con su trazo de color\n        if(!s.startsWith(TT_SEP)){\n          if(j > 0){ add('tt-plain', s); return; }\n          const h = add('tt-serie');\n          const k = document.createElement('i'); k.className = 'tt-key';\n          k.style.background = col.borderColor || col.backgroundColor || 'currentColor';\n          h.appendChild(k); par(h, s);\n          return;\n        }\n        const p = s.split(TT_SEP);   // p[0] siempre vacío\n        if(p[1] === 'S'){   // cabecera de serie con su valor a la derecha\n          const h = add('tt-serie tt-serie-val');\n          const k = document.createElement('i'); k.className = 'tt-key';\n          k.style.background = col.borderColor || col.backgroundColor || 'currentColor';\n          h.appendChild(k); par(h, p[2]);\n          const val = par(h, p[3]); val.className = 'tt-serie-num';\n        }\n        else if(p[1] === 'C'){ add('tt-cap', p[2]); }\n        else if(p[1] === 'H'){ add('tt-hero', p[3]); add('tt-hero-lbl', p[2]); }\n        else if(p[1] === 'D'){ add('tt-badge ' + (p[3] === 'up' ? 'up' : 'down'),\n                                   (p[3] === 'up' ? '▲ ' : '▼ ') + p[2]); }\n        else if(p[1] === 'R'){ const r = add('tt-row'); par(r, p[2]); par(r, p[3]); }\n        else if(p[1] === 'G'){\n          const tn = +p[2], tx = +p[3], nv = (p[4] === '' ? null : +p[4]), color = p[5] || 'currentColor';\n          const lo = Math.min(tn, nv == null ? tn : nv), hi = Math.max(tx, nv == null ? tx : nv);\n          const m = (hi - lo) * 0.12 || 1, a = lo - m, z = hi + m;\n          const pc = x => ((x - a) / (z - a)) * 100;\n          const bar = add('tt-bar');\n          const seg = document.createElement('i');\n          seg.style.left = pc(tn) + '%';\n          seg.style.width = Math.max(pc(tx) - pc(tn), 2) + '%';\n          seg.style.background = color;\n          bar.appendChild(seg);\n          if(nv != null){ const t = document.createElement('b');\n            t.style.left = 'calc(' + pc(nv) + '% - 1px)'; bar.appendChild(t); }\n          // Los extremos nombran mín y máx; el del medio dice qué es la marca amarilla\n          const ends = add('tt-ends'); par(ends, p[6] || '');\n          if(p[8]){ const c = par(ends, p[8]); c.style.color = '#c98a00'; c.style.fontWeight = '700'; }\n          par(ends, p[7] || '');\n        }\n      });\n    });\n    el.replaceChildren(frag);\n  }catch(err){\n    // Nunca dejar al usuario sin tooltip por un fallo de formato.\n    // Sin depender de nada externo: si el respaldo fallara, no habría tooltip.\n    try{\n      el.textContent = (tooltip.body || []).map(b => (b.lines || []).join(' · '))\n                         .join('  |  ').split('\\x1f').join(' ');\n    }catch(_){ el.textContent = ''; }\n  }\n  const w = el.offsetWidth, h = el.offsetHeight;\n  let x = tooltip.caretX + 16;\n  if(x + w > chart.canvas.clientWidth) x = tooltip.caretX - w - 16;\n  el.style.left = Math.max(0, x) + 'px';\n  el.style.top = Math.max(0, Math.min(tooltip.caretY - h / 2, chart.canvas.clientHeight - h)) + 'px';\n  el.style.opacity = 1;\n}",
    "estado comparar + renderChartTooltip")
sub("      const multi = e.ctrlKey || e.metaKey; // Ctrl (o Cmd en Mac) = comparar varios",
    "      const multi = e.ctrlKey || e.metaKey || cmpMode; // Ctrl/Cmd, o el botón «➕ Varios» en táctil",
    "multi por toque")
sub("    const q = btn.dataset.quick;",
    "    const q = btn.dataset.quick;\n    if(q === 'cmp'){   // no toca la selección: solo cambia cómo se interpretan los toques siguientes\n      cmpMode = !cmpMode;\n      btn.classList.toggle('on', cmpMode);\n      return;\n    }",
    "handler modo comparar")
sub("        tooltip:{\n          filter: (item) => !item.dataset.isBand,",
    "        tooltip:{\n          enabled: false,               // lo pinta renderChartTooltip() en HTML\n          external: renderChartTooltip,\n          filter: (item) => !item.dataset.isBand,",
    "activar tooltip HTML")
sub("            const lbl = String(items[0].label);\n            // Comparativa de un mes concreto: el eje solo lleva el número de día → añadir el mes\n            if(/^\\d{1,2}$/.test(lbl) && curMonthFilter && /^\\d+$/.test(curMonthFilter)){\n              const Lt = (document.documentElement.lang === 'fr');\n              const mi = parseInt(curMonthFilter)-1;\n              return Lt ? lbl+' '+MONTHS_FULL_FR[mi].toLowerCase() : lbl+' de '+MONTHS_FULL_ES[mi].toLowerCase();\n            }\n            return lbl;",
    "            const Lt = (document.documentElement.lang === 'fr');\n            let lbl = String(items[0].label);\n            // Comparativa de un mes concreto: el eje solo lleva el número de día → añadir el mes\n            if(/^\\d{1,2}$/.test(lbl) && curMonthFilter && /^\\d+$/.test(curMonthFilter)){\n              const mi = parseInt(curMonthFilter)-1;\n              lbl = Lt ? lbl+' '+MONTHS_FULL_FR[mi].toLowerCase() : lbl+' de '+MONTHS_FULL_ES[mi].toLowerCase();\n            }\n            // Con un solo año seleccionado el eje no lo indica: completar la fecha\n            if(typeof curCompareYears !== 'undefined' && curCompareYears.size === 1){\n              const y = [...curCompareYears][0];\n              if(!new RegExp('\\\\b'+y+'\\\\b').test(lbl)) lbl += (Lt ? ' ' : ' de ') + y;\n            }\n            return lbl;",
    "título del tooltip")
sub("            if(item.dataset.isMeanLine){ if(v==null) return null; const u = (item.dataset.yAxisID==='y1') ? 'mm' : info.unit; return '➜ '+item.dataset.label+': '+v.toFixed(1)+' '+u + (item.dataset.serieMean!=null ? '  ['+(L?'moy. période':'media periodo')+' '+item.dataset.serieMean.toFixed(1)+(item.dataset.yAxisID==='y1'?' mm':'°')+']' : ''); }",
    "            if(item.dataset.isMeanLine){\n              const u = (item.dataset.yAxisID==='y1') ? 'mm' : info.unit;\n              // El desglose solo cabe (y solo aporta) cuando no se comparan varios años\n              const nReal = item.chart.data.datasets.filter(d => !d.isBand && !d.isMeanLine && d.data[item.dataIndex] != null).length;\n              const S = TT_SEP;\n              if(nReal > 1) return `${S}S${S}${item.dataset.label}${S}${v.toFixed(1)} ${u}`;\n              const filas = [item.dataset.label,\n                             `${S}R${S}${L?'Ce jour-là':'Ese día'}${S}${v.toFixed(1)} ${u}`];\n              if(item.dataset.serieMean != null)\n                filas.push(`${S}R${S}${L?'Moyenne de la période':'Media del periodo'}${S}${item.dataset.serieMean.toFixed(1)} ${u}`);\n              return filas;\n            }",
    "fila de media climatológica")
sub("            // Vista diaria comparativa: añadir máxima y mínima del día\n            if(item.dataset.dayTx || item.dataset.dayTn){\n              const di = item.dataIndex;\n              const tx = item.dataset.dayTx ? item.dataset.dayTx[di] : null;\n              const tn = item.dataset.dayTn ? item.dataset.dayTn[di] : null;\n              const extra = [];\n              if(tx != null) extra.push((L?'max':'máx')+' '+tx.toFixed(1)+'°');\n              if(tn != null) extra.push((L?'min':'mín')+' '+tn.toFixed(1)+'°');\n              const base = `${rankPrefix||''}${item.dataset.label}: ${v.toFixed(2)} ${info.unit}`;\n              const sm = (item.dataset.serieMean!=null) ? '  ['+(L?'moyenne':'media')+' '+item.dataset.serieMean.toFixed(1)+'°]' : '';\n              return (extra.length ? base+'  ('+extra.join(' · ')+')' : base) + sm;",
    "            // Vista diaria comparativa: el dato del día, con máxima, mínima y desviación\n            if(item.dataset.dayTx || item.dataset.dayTn){\n              const di = item.dataIndex, u = info.unit;\n              const tx = item.dataset.dayTx ? item.dataset.dayTx[di] : null;\n              const tn = item.dataset.dayTn ? item.dataset.dayTn[di] : null;\n              const cab = `${rankPrefix||''}${item.dataset.label}`;\n              const nReal = item.chart.data.datasets.filter(d => !d.isBand && !d.isMeanLine && d.data[di] != null).length;\n              // Comparando varios años el desglose no cabe: nombre + valor, y máx/mín debajo\n              if(nReal > 1){\n                const filas = [`${TT_SEP}S${TT_SEP}${cab}${TT_SEP}${v.toFixed(1)} ${u}`];\n                const ex = [];\n                if(tx != null) ex.push((L?'max':'máx')+' '+tx.toFixed(1)+' '+u);\n                if(tn != null) ex.push((L?'min':'mín')+' '+tn.toFixed(1)+' '+u);\n                if(ex.length) filas.push(`${TT_SEP}C${TT_SEP}${ex.join('  ·  ')}`);\n                return filas;\n              }\n              // Un solo año: desglose completo, jerarquizado por renderChartTooltip()\n              const S = TT_SEP;\n              const varLbl = (L ? info.label_fr : info.label).replace(/\\s*\\([^)]*\\)\\s*$/, '');\n              const ml = item.chart.data.datasets.find(d => d.isMeanLine);\n              const nv = ml ? ml.data[di] : null;\n              const filas = [cab, `${S}H${S}${varLbl}${S}${v.toFixed(1)} ${u}`];\n              if(nv != null){\n                const d = v - nv;\n                filas.push(`${S}D${S}${d >= 0 ? '+' : '−'}${Math.abs(d).toFixed(1)} ${u} ` +\n                           (d >= 0 ? (L?'au-dessus de la normale':'sobre lo normal')\n                                   : (L?'en dessous de la normale':'bajo lo normal')) +\n                           `${S}${d >= 0 ? 'up' : 'down'}`);\n              }\n              // Barra: recorrido del día (mín→máx) con la normal marcada en amarillo\n              if(tx != null && tn != null){\n                filas.push([`${S}G`, tn, tx, (nv == null ? '' : nv), item.dataset.borderColor || '',\n                            `${L?'min':'mín'} ${tn.toFixed(1)} ${u}`,\n                            `${L?'max':'máx'} ${tx.toFixed(1)} ${u}`,\n                            nv == null ? '' : `${L?'normale':'normal'} ${nv.toFixed(1)}`].join(S));\n              } else {\n                if(tx != null) filas.push(`${S}R${S}${L?'Maximale':'Máxima'}${S}${tx.toFixed(1)} ${u}`);\n                if(tn != null) filas.push(`${S}R${S}${L?'Minimale':'Mínima'}${S}${tn.toFixed(1)} ${u}`);\n              }\n              if(item.dataset.serieMean != null)\n                filas.push(`${S}R${S}${L?'Moyenne de la période':'Media del periodo'}${S}${item.dataset.serieMean.toFixed(1)} ${u}`);\n              return filas;\n            }",
    "desglose del día")

# ---------- Resultado ----------
if errores:
    print("❌ El generador NO ha escrito nada. Parches que no encajan:")
    for e in errores:
        print("   -", e)
    sys.exit(1)

with open(DESTINO, "w", encoding="utf-8") as f:
    f.write(txt)
print(f"✅ Generado {os.path.basename(DESTINO)} ({len(txt)/1024:.0f} KB)")
