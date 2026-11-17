# TrafficLive · Proyecto N° 55

**Árboles B+ y Grafos Pesados para reportar y evitar atascos en Santa Cruz de la Sierra**

Feria Científica FICCT – UAGRM · Estructura de Datos 2 · Docente: Ing. MSc. Juan Carlos Peinado Pereira

🌐 Demo en vivo: **https://trafficlive-uagrm.vercel.app**

Los ciudadanos reportan incidentes de tráfico con foto. Un **Árbol B+ con doble índice** (por id y por `(timestamp, id)`) guarda el historial y lo consulta en O(log n + k). La red vial real de la ciudad, tomada de OpenStreetMap, se modela como un **grafo pesado dirigido**; **A\*** recalcula la ruta cuando un reporte cambia el peso de una calle, y **BFS** propaga la congestión hacia las calles vecinas para el mapa de calor.

## Resultados medidos

| Métrica | Resultado |
|---|---|
| Búsqueda por ID, Árbol B+ frente a lista enlazada (100.000 reportes) | ×1.522 |
| Búsqueda por rango de 1 hora | ×119 |
| Nodos explorados por A* frente a Dijkstra, red real de Santa Cruz (3.517 intersecciones) | −48,8 %, con la misma ruta |
| Recálculo de ruta tras un reporte (peor caso, red real) | 19,8 ms |
| Compresión de fotos en el navegador (5 fotos reales) | de 3.552 KB a 58 KB (−98,3 %) |

## Estructura

```
pagina-web/        Sitio publicado en Vercel (HTML, CSS y JS sin frameworks)
  js/bplus.js      Árbol B+ en JavaScript (inserción con split, búsqueda y rango por hojas enlazadas)
  js/app.js        Grafo dirigido, Dijkstra, A*, BFS, reportes, votos y compresión de imágenes
  data/            Red vial real de Santa Cruz (generada desde OpenStreetMap)
informe/codigo/    Implementaciones en Python, pruebas, benchmark y generador del informe
  arbol_bplus.py   Árbol B+ desde cero (inserción, búsqueda, rango y eliminación con préstamo y fusión)
  grafo_trafico.py Grafo pesado dirigido: Dijkstra, A*, BFS y aplicar_reporte(bidireccional=False)
  red_osm.py       Convierte las vías de OpenStreetMap en grafo dirigido y mide Dijkstra frente a A*
  benchmark.py     Experimento reproducible (semilla 2026)
informe/           Informe final (APA 7) en PDF y DOCX
diseno/            Logo, banner (80 × 200 cm) y credenciales
```

## Reproducir los experimentos

```bash
cd informe/codigo
python pruebas_correccion.py                 # Árbol B+ contra un diccionario; A* contra Dijkstra
python benchmark.py resultados.json          # cuadrícula sintética
python figuras.py resultados.json ../figuras

# Red real: descargar las vías principales con la API Overpass y construir el grafo
curl --data-urlencode 'data=[out:json][timeout:120];(way["highway"~"^(motorway|trunk|primary|secondary|tertiary|motorway_link|trunk_link|primary_link|secondary_link)$"](-17.835,-63.235,-17.735,-63.130););out body geom;' \
     https://overpass-api.de/api/interpreter -o santa_cruz_vias.json
python red_osm.py santa_cruz_vias.json resultados_osm.json ../../pagina-web/data/red_santa_cruz.json
```

La compresión de imágenes se mide abriendo `informe/codigo/medir_compresion.html` en el navegador, servida junto a las fotos en `/datos_fotos/`.

## Equipo

| Integrante | Carrera | ORCID |
|---|---|---|
| Estaca Paco Sergio | Ingeniería Informática | [0009-0006-5377-8272](https://orcid.org/0009-0006-5377-8272) |
| Cruz Rojas Annett Alejandra | Ingeniería Informática | en trámite |
| Perez Sandoval Wendy Nicol | Ingeniería Informática | [0009-0004-3923-5445](https://orcid.org/0009-0004-3923-5445) |
| Murguia Duran Paola Andrea | Ingeniería en Sistemas | en trámite |
| Roca Camacho Adria Fernando | Ingeniería en Sistemas | en trámite |

## Créditos y licencias de datos

- Datos viales y mapa base: © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), licencia ODbL.
- Bibliotecas: [Leaflet](https://leafletjs.com/), [Leaflet.heat](https://github.com/Leaflet/Leaflet.heat), [Chart.js](https://www.chartjs.org/).
- Fotografías usadas para medir la compresión: Wikimedia Commons, con licencia libre. No se incluyen en el repositorio.
