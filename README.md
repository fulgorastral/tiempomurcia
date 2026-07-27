# Murcia y Caravaca · Explorador de datos meteorológicos

Aplicación web para explorar la serie diaria de **Murcia (7178I, desde 1984)** y
**Caravaca de la Cruz (7119B, desde 2009)**: temperaturas, precipitación, viento, humedad,
insolación, climogramas, comparación entre años y efemérides de olas de calor y de frío.

Las olas se detectan sobre el periodo de referencia **1991–2020**, la normal climática vigente
de la OMM: 3 días consecutivos por encima del percentil 95 de las máximas de julio y agosto
(calor) o por debajo del percentil 5 de las mínimas de enero y febrero (frío).

Todo el cálculo pasa en el navegador; los datos viven en `murcia_data.js`.

## La web se actualiza sola

`.github/workflows/actualizar-datos.yml` se ejecuta **cada día a las 05:40 UTC** (07:40 en España
en horario de verano) y:

1. Baja de **AEMET OpenData** los días nuevos de las dos estaciones (modo incremental: solo lo que
   falta, más 10 días de solape para recoger correcciones tardías).
2. Regenera `informe_olas_calor.html`, `informe_olas_frio.html` y `efemerides.js`.
3. Commitea los cambios y **republica la web en GitHub Pages**.

AEMET publica los valores climatológicos diarios con **unos 4 días de retardo**, así que lo normal
es que la web vaya siempre unos días por detrás de hoy. La cabecera indica *datos hasta el…* y
*actualizado el…* para que se vea de un vistazo.

Si algún día AEMET no responde (se satura con frecuencia y devuelve 429), **no se toca la serie**:
la web se republica con los datos que ya había y al día siguiente se reintenta. El workflow se
marca en rojo para que llegue el aviso por email. Open-Meteo/ERA5 solo entra como red de emergencia
si no hubiera ningún dato, porque son datos de modelo y no medidas reales de la estación.

### Puesta en marcha (una sola vez)

| Paso | Dónde |
|---|---|
| Guardar la clave de AEMET como secret llamado `AEMET_API_KEY` | Settings › Secrets and variables › Actions |
| Poner el origen de Pages en **GitHub Actions** | Settings › Pages › Source |
| Primera carga completa de la serie AEMET | Actions › *Actualizar datos y publicar web* › Run workflow, marcando **completo** |

La clave se consigue gratis en <https://opendata.aemet.es/centrodedescargas/obtencionAPIKey>.
Nunca se sube al repositorio: en local vive en `aemet_api_key.txt`, que está en `.gitignore`.

> GitHub desactiva los workflows programados en repos sin actividad durante 60 días. Si algún día
> deja de actualizarse, basta con reactivarlo desde la pestaña Actions.

## Uso en local

Doble clic en `actualizar_murcia.bat` (necesita Python 3): descarga los datos, regenera las
efemérides y abre `Murcia_app_explorador.html`.

| Archivo | Qué hace |
|---|---|
| `descargar_aemet_murcia.py` | Descarga la serie de AEMET → `murcia_data.js` + un CSV por estación. `--completo` rebaja todo desde 1984 |
| `descargar_openmeteo_murcia.py` | Plan B sin API Key: reanálisis ERA5 vía Open-Meteo (datos de modelo, no oficiales) |
| `generar_efemerides.py` | Detecta olas de calor y de frío → los dos informes HTML + `efemerides.js` |
| `generar_app_murcia.py` | Regenera `Murcia_app_explorador.html` a partir de la app de Albertville |

## Fuentes

- **AEMET OpenData** — valores climatológicos diarios de las estaciones 7178I y 7119B.
- **Open-Meteo / ERA5** — solo como respaldo; son datos de reanálisis (modelo), no medidas.
