# TrafficLive · Proyecto N° 55

**Árboles B+ y Grafos Pesados para reportar y evitar atascos en Santa Cruz de la Sierra**

Feria Facultativa FICCT 2-2026 – UAGRM · Estructura de Datos 2 · Docente tutor: Ing. MSc. Juan Carlos Peinado Pereira

🌐 **Demo en vivo:** https://trafficlive-uagrm.vercel.app  
📄 **Informe final:** [documentos/05_informe_final/Informe_TrafficLive_Final.pdf](documentos/05_informe_final/Informe_TrafficLive_Final.pdf)

Los ciudadanos reportan incidentes de tráfico con foto. Un **Árbol B+ con doble índice** (por id y por `(timestamp, id)`) guarda el historial y lo consulta en O(log n + k). La red vial real de la ciudad, tomada de OpenStreetMap, se modela como un **grafo pesado dirigido**: **A\*** recalcula la ruta cuando un reporte cambia el peso de una calle, y **BFS** propaga la congestión hacia las calles vecinas para el mapa de calor.

## Resultados medidos

| Métrica | Resultado |
|---|---|
| Búsqueda por ID: Árbol B+ frente a lista enlazada (100.000 reportes) | ×1.522 |
| Búsqueda por rango de 1 hora | ×119 |
| Nodos explorados por A* frente a Dijkstra (red real de Santa Cruz, 3.517 intersecciones) | −48,8 %, con la misma ruta |
| Recálculo de ruta tras un reporte (peor caso, red real) | 19,8 ms |
| Compresión de fotos en el navegador (5 fotos reales) | de 3.552 KB a 58 KB (−98,3 %) |

## Estructura del repositorio

```
documentos/                    Evolución del informe, revisión por revisión
  01_primera_presentacion/     Informe de la primera presentación (octubre de 2026)
  02_primera_revision/         Informe de evaluación y tutoría del 13 de octubre de 2026
  03_segunda_presentacion/     Informe corregido de la segunda presentación (PDF y DOCX)
  04_segunda_revision/         Informe de revisión y mejora de noviembre de 2026
  05_informe_final/            Informe final en APA 7 (PDF y DOCX)
investigacion/
  codigo/                      Implementaciones propias en Python, pruebas, benchmark y generador del informe
    arbol_bplus.py             Árbol B+ desde cero (inserción, búsqueda, rango y eliminación con préstamo y fusión)
    grafo_trafico.py           Grafo pesado dirigido: Dijkstra, A*, BFS y aplicar_reporte(bidireccional=False)
    red_osm.py                 Convierte las vías de OpenStreetMap en grafo dirigido y mide Dijkstra frente a A*
    benchmark.py               Experimento reproducible (semilla 2026)
    pruebas_correccion.py      Pruebas de oráculo
    medir_compresion.html      Medición de la compresión de imágenes en el navegador
    resultados*.json           Resultados medidos
  figuras/                     Gráficos, diagramas y capturas usados en el informe
pagina-web/                    Sitio publicado en Vercel (HTML, CSS y JS, sin frameworks)
  js/bplus.js                  Árbol B+ en JavaScript
  js/app.js                    Grafo dirigido, A*, BFS, reportes, votos y compresión de imágenes
  data/red_santa_cruz.json     Red vial real de Santa Cruz (generada desde OpenStreetMap)
diseno/                        Logo, banner de 80 × 200 cm y credenciales del equipo
```

## Reproducir los experimentos

```bash
cd investigacion/codigo
python pruebas_correccion.py                 # Árbol B+ contra un diccionario; A* contra Dijkstra
python benchmark.py resultados.json          # cuadrícula sintética
python figuras.py resultados.json ../figuras

# Red real: descargar las vías principales con la API Overpass y construir el grafo dirigido
curl --data-urlencode 'data=[out:json][timeout:120];(way["highway"~"^(motorway|trunk|primary|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link)$"](-17.835,-63.235,-17.735,-63.130););out body geom;' \
     https://overpass-api.de/api/interpreter -o santa_cruz_vias.json
python red_osm.py santa_cruz_vias.json resultados_osm.json ../../pagina-web/data/red_santa_cruz.json
```

## Equipo

| Integrante | Carrera | ORCID |
|---|---|---|
| Estaca Paco Sergio | Ingeniería Informática | [0009-0006-5377-8272](https://orcid.org/0009-0006-5377-8272) |
| Cruz Rojas Annett Alejandra | Ingeniería Informática | [0009-0001-2285-3261](https://orcid.org/0009-0001-2285-3261) |
| Perez Sandoval Wendy Nicol | Ingeniería Informática | [0009-0004-3923-5445](https://orcid.org/0009-0004-3923-5445) |
| Murguia Duran Paola Andrea | Ingeniería en Sistemas | [0009-0005-3107-5886](https://orcid.org/0009-0005-3107-5886) |
| Roca Camacho Adria Fernando | Ingeniería en Sistemas | [0009-0006-1540-7462](https://orcid.org/0009-0006-1540-7462) |

## Créditos y licencias de datos

- Datos viales y mapa base: © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), licencia ODbL.
- Bibliotecas: [Leaflet](https://leafletjs.com/), [Leaflet.heat](https://github.com/Leaflet/Leaflet.heat), [Chart.js](https://www.chartjs.org/).
- Fotografías usadas para medir la compresión: Wikimedia Commons, con licencia libre. No se incluyen en el repositorio.
