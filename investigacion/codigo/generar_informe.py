"""Genera el informe (segunda presentación) en .docx a partir de los resultados medidos.
Uso: python generar_informe.py salida.docx [paginas_indice.json]"""
import json
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "..", "figuras")
RES = json.load(open(os.path.join(BASE, "resultados.json"), encoding="utf-8"))
PAGINAS = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else {}
URL_WEB = "https://trafficlive-uagrm.vercel.app"
REPO = "https://github.com/Kato-001/TrafficLive"
AZUL = RGBColor(0x1F, 0x3B, 0x63)

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(27.94), Cm(21.59)          # carta
sec.top_margin = sec.bottom_margin = Cm(2.54)
sec.left_margin = sec.right_margin = Cm(2.54)

st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 2.0
st.paragraph_format.space_after = Pt(0)
for nombre, tam in (("Heading 1", 12), ("Heading 2", 12), ("Heading 3", 12)):
    h = doc.styles[nombre]
    h.font.name, h.font.size, h.font.bold, h.font.color.rgb = "Times New Roman", Pt(tam), True, RGBColor(0, 0, 0)
    h.font.italic = nombre == "Heading 3"
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    h.element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    h.element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    for atr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        h.element.rPr.rFonts.attrib.pop(qn(atr), None)
    h.paragraph_format.space_before = Pt(0)
    h.paragraph_format.space_after = Pt(0)
    h.paragraph_format.line_spacing = 2.0
    h.paragraph_format.keep_with_next = True

TITULOS_INDICE = []          # (nivel, texto) en orden, para el índice estático
n_fig = n_tab = 0


def es(x, d=1):
    """Número en formato español: 1.234,5"""
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def agregar_runs(p, texto, tam=None, italica=False):
    """Admite **negrita** y _cursiva_ simples dentro del texto."""
    import re
    for parte in re.split(r"(\*\*[^*]+\*\*|(?<!\w)_[^_]+_(?!\w))", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            r = p.add_run(parte[2:-2]); r.bold = True
        elif parte.startswith("_") and parte.endswith("_") and len(parte) > 2:
            r = p.add_run(parte[1:-1]); r.italic = True
        else:
            r = p.add_run(parte)
        if tam:
            r.font.size = Pt(tam)
        if italica:
            r.italic = True
    return p


def P(texto, alinear=WD_ALIGN_PARAGRAPH.JUSTIFY, sangria=True, tam=None):
    p = doc.add_paragraph()
    p.alignment = alinear
    if sangria and alinear == WD_ALIGN_PARAGRAPH.JUSTIFY:
        p.paragraph_format.first_line_indent = Cm(1.27)
    return agregar_runs(p, texto, tam)


def viñetas(items, estilo="List Bullet"):
    for it in items:
        p = doc.add_paragraph(style=estilo)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(0)
        agregar_runs(p, it)


def numerada(items):
    for i, it in enumerate(items, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Pt(0)
        agregar_runs(p, f"{i}. " + it)


def salto():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def H1(texto, indice=True, nueva_pagina=True):
    if nueva_pagina:
        salto()
    h = doc.add_heading(texto, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER          # APA nivel 1: centrado y en negrita
    if indice:
        TITULOS_INDICE.append((1, texto))


def H2(texto):
    doc.add_heading(texto, level=2)
    TITULOS_INDICE.append((2, texto))


def H3(texto):
    doc.add_heading(texto, level=3)
    TITULOS_INDICE.append((3, texto))


def sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def bordes_apa(t):
    """Tabla APA 7: línea arriba, línea bajo el encabezado y línea al final; sin líneas verticales."""
    tblPr = t._tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "bottom"):
        b = OxmlElement(f"w:{lado}"); b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "8"); b.set(qn("w:color"), "000000")
        bordes.append(b)
    for lado in ("left", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}"); b.set(qn("w:val"), "nil"); bordes.append(b)
    tblPr.append(bordes)
    for c in t.rows[0].cells:
        tcPr = c._tc.get_or_add_tcPr()
        tcb = OxmlElement("w:tcBorders"); b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6"); b.set(qn("w:color"), "000000")
        tcb.append(b); tcPr.append(tcb)


def leyenda_tabla(titulo):
    global n_tab
    n_tab += 1
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(f"Tabla {n_tab}"); r.bold = True
    p2 = doc.add_paragraph()
    p2.paragraph_format.keep_with_next = True
    p2.paragraph_format.line_spacing = 1.15
    p2.add_run(titulo).italic = True
    return n_tab


def tabla(encabezados, filas, anchos=None, titulo=None, fuente=None, tam=10, alinear_num=True):
    if titulo:
        leyenda_tabla(titulo)
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(encabezados):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        r = p.add_run(h); r.bold = True; r.font.size = Pt(tam)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
    for fila in filas:
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = ""
            p = celdas[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            agregar_runs(p, str(v), tam)
            texto = str(v).replace("*", "")
            if alinear_num and len(texto) < 20 and (texto[:1].isdigit() or (texto[:1] != "" and texto[:1] in "×<≥+−")):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    bordes_apa(t)
    # repetir encabezado si la tabla salta de página
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    if anchos:
        for fila in t.rows:
            for i, w in enumerate(anchos):
                fila.cells[i].width = Cm(w)
    if fuente:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        agregar_runs(p, "_Nota._ " + fuente, 9.5)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def figura(archivo, titulo, ancho=15.5, fuente="Elaboración propia."):
    global n_fig
    n_fig += 1
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.line_spacing = 1.15
    p.add_run(f"Figura {n_fig}").bold = True
    p2 = doc.add_paragraph()
    p2.paragraph_format.keep_with_next = True
    p2.paragraph_format.line_spacing = 1.15
    p2.add_run(titulo).italic = True
    pi = doc.add_paragraph()
    pi.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pi.paragraph_format.keep_with_next = True
    pi.add_run().add_picture(os.path.join(FIG, archivo), width=Cm(ancho))
    pn = doc.add_paragraph()
    pn.paragraph_format.line_spacing = 1.0
    agregar_runs(pn, "_Nota._ " + fuente, 9.5)
    return n_fig


def codigo(texto, tam=8):
    for linea in texto.rstrip("\n").split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.3)
        r = p.add_run(linea if linea else " ")
        r.font.name = "Courier New"; r.font.size = Pt(tam)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "F3F5F8"); pPr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def campo(parrafo, instruccion):
    for tipo, texto in (("begin", None), (None, instruccion), ("separate", None), (None, "1"), ("end", None)):
        r = parrafo.add_run()
        if tipo:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), tipo); r._r.append(fc)
        elif texto == instruccion:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instruccion; r._r.append(it)
        else:
            r.text = texto


# ======================================================================== datos derivados
R, G = RES["reportes"], RES["grafo"]
OSM = json.load(open(os.path.join(BASE, "resultados_osm.json"), encoding="utf-8"))
FOTOS = json.load(open(os.path.join(BASE, "resultados_compresion.json"), encoding="utf-8"))
red_osm = 1 - OSM["expandidos_a_estrella"] / OSM["expandidos_dijkstra"]
red_t_osm = 1 - OSM["a_estrella_ms"] / OSM["dijkstra_ms"]
foto_red = sum(f["reduccion_pct"] for f in FOTOS) / len(FOTOS)
foto_orig = sum(f["original_kb"] for f in FOTOS) / len(FOTOS)
foto_comp = sum(f["comprimida_kb"] for f in FOTOS) / len(FOTOS)
r100, g10k = R[-1], G[-1]
x_id = r100["busqueda_id_lista_ms"] / r100["busqueda_id_bplus_ms"]
x_rango = r100["rango_lista_ms"] / r100["rango_bplus_ms"]
red_exp = 1 - g10k["expandidos_a_estrella"] / g10k["expandidos_dijkstra"]
red_t = 1 - g10k["a_estrella_ms"] / g10k["dijkstra_ms"]
red_exp_min = min(1 - g["expandidos_a_estrella"] / g["expandidos_dijkstra"] for g in G if g["nodos"] >= 1000)
rec_max = max(g["recalculo_max_ms"] for g in G)
us = lambda ms: es(ms * 1000, 1)

# ======================================================================== CARÁTULA
pgNum = OxmlElement("w:pgNumType"); pgNum.set(qn("w:start"), "1"); sec._sectPr.append(pgNum)
pie = sec.header.paragraphs[0]
pie.alignment = WD_ALIGN_PARAGRAPH.RIGHT
campo(pie, "PAGE")

for texto, tam, negrita, antes in (
    ("UNIVERSIDAD AUTÓNOMA GABRIEL RENÉ MORENO", 16, True, 0),
    ("FACULTAD DE INGENIERÍA EN CIENCIAS DE LA COMPUTACIÓN Y TELECOMUNICACIONES", 13, True, 4),
    ("(FICCT)", 12, False, 0),
):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(antes); p.paragraph_format.line_spacing = 1.15
    r = p.add_run(texto); r.bold = negrita; r.font.size = Pt(tam); r.font.color.rgb = AZUL
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(36)
r = p.add_run("PROYECTO N° 55"); r.bold = True; r.font.size = Pt(13)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(10)
r = p.add_run("TrafficLive"); r.bold = True; r.font.size = Pt(26); r.font.color.rgb = AZUL
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.line_spacing = 1.2
r = p.add_run("Árboles B+ y Grafos Pesados para reportar y evitar atascos en Santa Cruz de la Sierra")
r.bold = True; r.font.size = Pt(14)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(8)
r = p.add_run("Informe final de investigación"); r.italic = True; r.font.size = Pt(12)

p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(30); p.paragraph_format.left_indent = Cm(2)
p.paragraph_format.line_spacing = 1.3
p.add_run("Área: ").bold = True; p.add_run("Estructura de Datos 2\n")
p.add_run("Docente: ").bold = True; p.add_run("Ing. MSc. Juan Carlos Peinado Pereira\n")
p.add_run("Carreras: ").bold = True; p.add_run("Ingeniería Informática e Ingeniería en Sistemas\n")
p.add_run("Estudiantes:").bold = True
for nombre in ("Estaca Paco Sergio", "Cruz Rojas Annett Alejandra", "Perez Sandoval Wendy Nicol",
               "Murguia Duran Paola Andrea", "Roca Camacho Adria Fernando"):
    q = doc.add_paragraph(style="List Bullet"); q.paragraph_format.left_indent = Cm(3)
    q.paragraph_format.space_after = Pt(0); q.paragraph_format.line_spacing = 1.2
    q.add_run(nombre)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(24)
r = p.add_run("Santa Cruz de la Sierra – Bolivia\nNoviembre de 2026"); r.bold = True

# ======================================================================== ORCID + LOGO
AUTORES = [   # nombre, carrera, ORCID
    ("Estaca Paco Sergio", "Ingeniería Informática", "0009-0006-5377-8272"),
    ("Cruz Rojas Annett Alejandra", "Ingeniería Informática", "0009-0001-2285-3261"),
    ("Perez Sandoval Wendy Nicol", "Ingeniería Informática", "0009-0004-3923-5445"),
    ("Murguia Duran Paola Andrea", "Ingeniería en Sistemas", "0009-0005-3107-5886"),
    ("Roca Camacho Adria Fernando", "Ingeniería en Sistemas", "0009-0006-1540-7462"),
]


def hipervinculo(parrafo, url, texto, tam=10):
    rid = parrafo.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                                 is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rid)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    for etiqueta, valor in (("w:color", "1F5FA8"), ("w:u", "single"), ("w:sz", str(int(tam * 2)))):
        e = OxmlElement(etiqueta); e.set(qn("w:val"), valor); rPr.append(e)
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = texto; r.append(t)
    h.append(r); parrafo._p.append(h)


H1("Identificadores ORCID de los autores")
P("ORCID (_Open Researcher and Contributor ID_) es un identificador digital gratuito y persistente que distingue de "
  "manera única a cada investigador y conecta su nombre con sus trabajos académicos, aunque existan otras personas con "
  "nombres similares (ORCID, s.f.). Los autores de este proyecto se identifican de la siguiente manera:")
t_orcid = tabla(["N°", "Nombre completo", "Carrera", "ORCID"],
                [[str(i), n, c, ""] for i, (n, c, _) in enumerate(AUTORES, 1)], [0.9, 5.0, 4.1, 6.5], tam=10)
t_orcid.autofit = False                      # anchos fijos para que el enlace del ORCID quepa en una línea
for i, w in enumerate([0.9, 5.0, 4.1, 6.5]):
    t_orcid.columns[i].width = Cm(w)
fijo = OxmlElement("w:tblLayout"); fijo.set(qn("w:type"), "fixed"); t_orcid._tbl.tblPr.append(fijo)
for fila in t_orcid.rows:
    fila.height = Cm(0.8)
    for c in fila.cells:
        c.vertical_alignment = 1
for fila, (_, _, orcid) in zip(t_orcid.rows[1:], AUTORES):
    p = fila.cells[3].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if orcid:
        hipervinculo(p, "https://orcid.org/" + orcid, "https://orcid.org/" + orcid)
    else:
        r = p.add_run("Pendiente"); r.font.size = Pt(10); r.italic = True
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(24); p.paragraph_format.line_spacing = 1.0
p.add_run().add_picture(os.path.join(FIG, "logo_trafficlive.png"), width=Cm(6.5))
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.line_spacing = 1.0
r = p.add_run("Logo del proyecto de investigación"); r.italic = True; r.font.size = Pt(10)

# ======================================================================== PRELIMINARES
H1("Agradecimiento", indice=True)
P("Expresamos nuestro más sincero agradecimiento a nuestro docente de la asignatura Estructura de Datos 2, Ing. MSc. Juan Carlos "
  "Peinado Pereira, por su orientación, sus conocimientos y la dedicación con la que revisó la primera versión de este trabajo. "
  "Sus observaciones sobre la taxonomía de la investigación, el marco metodológico y la presentación de los resultados guiaron "
  "directamente las mejoras de esta segunda presentación.")
P("Extendemos nuestro reconocimiento a los compañeros del equipo, cuya dedicación, esfuerzo y colaboración hicieron posible "
  "la realización de esta investigación, y a las personas que probaron el prototipo y aportaron sugerencias para mejorar su uso.")

H1("Resumen")
P("El crecimiento acelerado de Santa Cruz de la Sierra —1.606.671 habitantes según el Censo 2024— y de su parque automotor "
  f"—973.537 vehículos registrados en el departamento a diciembre de 2025, el 36,4 % del total nacional— agrava la congestión "
  "en su red vial de anillos y radiales. Los sistemas de navegación actuales dependen de datos pasivos de GPS y no ofrecen a la "
  "comunidad un historial consultable de incidentes verificables. Este trabajo, de tipo aplicado y con diseño experimental "
  "computacional, desarrolla TrafficLive: una aplicación web colaborativa en la que los ciudadanos reportan incidentes con "
  "imágenes geolocalizadas. Los reportes se indexan en un Árbol B+ implementado desde cero (orden M = 5) y la red vial se modela "
  "como un Grafo Pesado dirigido cuyos pesos se actualizan con cada reporte; las rutas se calculan con Dijkstra y A*, y la "
  "congestión se propaga a las calles vecinas mediante BFS. Las mediciones, reproducibles y con semilla fija, muestran que con "
  f"100.000 reportes el Árbol B+ es {es(x_id, 0)} veces más rápido que una lista enlazada en la búsqueda por identificador y "
  f"{es(x_rango, 0)} veces más rápido en la búsqueda por rango de una hora, con complejidad O(log n + k) frente a O(n). En "
  f"grafos de hasta 10.000 intersecciones, A* obtiene la misma ruta óptima que Dijkstra expandiendo un {es(red_exp * 100, 0)} % "
  f"menos de nodos, y el recálculo de ruta tras un reporte tarda como máximo {es(rec_max, 1)} ms. En la red vial real de la ciudad, tomada de OpenStreetMap (3.517 "
  f"intersecciones), A* explora un {es(red_osm * 100, 1)} % menos de nodos, y la compresión en el cliente reduce las fotografías "
  f"un {es(foto_red, 1)} %. Se aceptan las tres hipótesis "
  "planteadas y se concluye que la combinación de estructuras de datos no lineales con la participación ciudadana es una "
  "solución viable y de bajo costo para la gestión del tráfico urbano.")
P("_Palabras clave:_ estructuras de datos, Árbol B+, grafos pesados, algoritmo de Dijkstra, algoritmo A*, tráfico vehicular, "
  "crowdsourcing, Santa Cruz de la Sierra.")

H1("Abstract")
P("The rapid growth of Santa Cruz de la Sierra, Bolivia —1,606,671 inhabitants according to the 2024 Census— and of its vehicle "
  "fleet —973,537 vehicles registered in the department by December 2025, 36.4% of the national total— worsens congestion in "
  "its ring-and-radial road network. Current navigation systems rely on passive GPS data and do not give the community a "
  "searchable history of verifiable incidents. This applied study, with a computational experimental design, develops "
  "TrafficLive, a collaborative web application where citizens report incidents with geotagged images. Reports are indexed in "
  "a B+ Tree implemented from scratch (order M = 5), and the road network is modeled as a directed weighted graph whose edge "
  "weights are updated with every report; routes are computed with Dijkstra and A*, and congestion is propagated to neighboring "
  "streets using BFS. Reproducible, fixed-seed measurements show that with 100,000 reports the B+ Tree is "
  f"{x_id:,.0f} times faster than a linked list for lookup by identifier and {x_rango:,.0f} times faster for a one-hour range "
  f"query, with O(log n + k) versus O(n) complexity. On graphs of up to 10,000 intersections, A* returns the same optimal route "
  f"as Dijkstra while expanding {red_exp * 100:.0f}% fewer nodes, and re-routing after a report takes at most {rec_max:.1f} ms. On the real road network of the city "
  f"(OpenStreetMap, 3,517 intersections), A* expands {red_osm * 100:.1f}% fewer nodes, and client-side compression shrinks "
  f"photos by {foto_red:.1f}%. "
  "All three hypotheses are accepted. We conclude that combining non-linear data structures with citizen participation is a "
  "viable, low-cost solution for urban traffic management.")
P("_Keywords:_ data structures, B+ Tree, weighted graphs, Dijkstra's algorithm, A* algorithm, vehicular traffic, "
  "crowdsourcing, Santa Cruz de la Sierra.")

# ======================================================================== ÍNDICE (estático, paginado en una segunda pasada)
H1("Índice", indice=False)
MARCA_INDICE = len(doc.paragraphs)
INDICE_PARRAFOS = []


def reservar_indice(n):
    for _ in range(n):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(3)
        INDICE_PARRAFOS.append(p)


reservar_indice(int(sys.argv[3]) if len(sys.argv) > 3 else 90)

# ======================================================================== INTRODUCCIÓN
H1("Introducción")
P("La congestión vehicular es uno de los principales problemas de movilidad de las ciudades latinoamericanas. Un estudio del "
  "Banco Interamericano de Desarrollo estimó que, en diez áreas metropolitanas de la región, los costos de la congestión "
  "equivalen a entre el 0,55 % y el 1,12 % del producto interno bruto local (Calatayud et al., 2021). Santa Cruz de la Sierra, "
  "la ciudad más poblada de Bolivia, concentra además el mayor parque automotor del país (Instituto Nacional de Estadística "
  "[INE], citado en eju.tv, 2026a), y su estructura radio-concéntrica de anillos y radiales hace que un solo tramo bloqueado "
  "obligue a desvíos largos.")
P("Los sistemas de navegación como Google Maps o Waze ofrecen información de tráfico en tiempo real, pero sus datos no están "
  "disponibles para que la comunidad o el municipio los consulten libremente, no conservan un historial abierto de incidentes "
  "por calle y hora, y no permiten verificar los reportes con imágenes. El presente proyecto propone **TrafficLive**, una "
  "aplicación web colaborativa que aplica dos estructuras de datos centrales de la asignatura Estructura de Datos 2: el "
  "**Árbol B+**, para almacenar y consultar eficientemente el historial de reportes, y el **Grafo Pesado**, para representar la "
  "red vial y recalcular rutas óptimas cuando cambian las condiciones de las calles.")
P("Esta versión final incorpora las observaciones de la tutoría del 13 de octubre de 2026: se contextualizó el "
  "problema con datos reales de Santa Cruz de la Sierra, se formularon hipótesis contrastables, se añadió un marco metodológico "
  "con variables e indicadores, se reemplazaron los valores estimados por mediciones reales obtenidas con implementaciones "
  "propias, y los resultados se presentan en gráficos de líneas. También atiende la revisión de noviembre de 2026: se "
  "alineó la pregunta de investigación con lo construido, se precisó la doble indexación del Árbol B+, se midió la "
  "compresión de imágenes en KB y se validaron los algoritmos sobre la red vial real de Santa Cruz, tomada de "
  "OpenStreetMap. El detalle de cada corrección se resume en el Anexo A. "
  f"El prototipo está publicado como página web interactiva en {URL_WEB}.")
P("El documento se organiza así: el capítulo 1 presenta los antecedentes; el 2, el planteamiento del problema, la hipótesis y la "
  "justificación; el 3, los objetivos; el 4, el marco teórico; el 5, el marco metodológico; el 6, la propuesta de solución; el 7, "
  "el desarrollo e implementación; y el 8, las pruebas y resultados. Finalmente se presentan las conclusiones, las "
  "recomendaciones, las referencias y los anexos.")

# ======================================================================== 1. ANTECEDENTES
H1("1. Antecedentes")
H2("1.1 Problemática del tráfico urbano en ciudades latinoamericanas")
P("La motorización de las ciudades de América Latina y el Caribe ha crecido más rápido que su infraestructura vial. Calatayud "
  "et al. (2021) analizaron diez áreas metropolitanas de la región con datos de 2019 y estimaron que la congestión representa "
  "costos de entre el 0,55 % (San Salvador) y el 1,12 % (Buenos Aires y São Paulo) del PIB local, por el tiempo perdido, el "
  "mayor consumo de combustible y las emisiones. Estas pérdidas se concentran en las horas pico y en los corredores que "
  "conectan las zonas residenciales con los centros de actividad.")
P("Bolivia sigue la misma tendencia: su parque automotor se quintuplicó en casi veinte años (Correo del Sur, 2023) y alcanzó "
  "2.672.176 vehículos en 2025, un 3,4 % más que en 2024, según datos del Registro Único para la Administración Tributaria "
  "Municipal (RUAT) procesados por el INE (eju.tv, 2026b). Las motocicletas son la clase más numerosa, con 931.205 unidades "
  "(34,8 % del total nacional).")

H2("1.2 Sistemas de navegación actuales y sus limitaciones")
viñetas([
    "**Google Maps:** su API para JavaScript ofrece la capa _TrafficLayer_, que muestra el estado del tráfico como imagen sobre "
    "el mapa, pero no entrega los datos de congestión para que una aplicación los procese (Google, s.f.).",
    "**Waze:** recibe reportes de sus usuarios y comparte alertas y atascos con gobiernos e instituciones mediante el programa "
    "Waze for Cities, que requiere un convenio formal y está orientado a entidades públicas (Waze, s.f.).",
    "**Limitación común:** ninguno de los dos ofrece a la comunidad local un historial abierto de incidentes que se pueda "
    "consultar por calle y franja horaria, ni un mecanismo de verificación con fotografías geolocalizadas.",
])

H2("1.3 El crowdsourcing como herramienta de participación ciudadana")
P("El término _crowdsourcing_ describe la obtención de información o trabajo a partir de una multitud de personas conectadas "
  "en red (Howe, 2006). En movilidad urbana existen casos exitosos: Waze construye su mapa de incidentes con reportes de "
  "conductores, OpenStreetMap elabora la cartografía libre del mundo con voluntarios (Haklay y Weber, 2008) y FixMyStreet "
  "permite reportar problemas de la vía pública a los municipios. Sus ventajas son el bajo costo, la actualización constante "
  "y la cobertura amplia; su principal desafío es la calidad de los datos, que exige mecanismos de validación.")

H2("1.4 Estructuras de datos aplicadas a sistemas de tráfico")
viñetas([
    "Los Árboles B y B+ son la estructura de índice estándar en los sistemas de bases de datos, porque minimizan los accesos a "
    "disco y permiten recorridos ordenados (Bayer y McCreight, 1972; Comer, 1979; Elmasri y Navathe, 2016).",
    "Los grafos pesados son la representación natural de una red de transporte: las intersecciones son vértices y los tramos de "
    "calle, aristas con un costo de viaje (Cormen et al., 2009).",
    "Los algoritmos de Dijkstra (1959) y A* (Hart et al., 1968) son la base del cálculo de caminos mínimos en navegación; los "
    "motores de rutas comerciales los aceleran con técnicas adicionales de preprocesamiento.",
])

# ======================================================================== 2. PLANTEAMIENTO
H1("2. Planteamiento del problema")
H2("2.1 Problema central")
P("Los sistemas de navegación disponibles no permiten que la comunidad contribuya con reportes verificables (con imágenes) "
  "sobre incidentes viales que queden registrados en un historial abierto, ni ofrecen un mecanismo eficiente para almacenar y "
  "consultar grandes volúmenes de reportes por rango de tiempo. Además, el cálculo de rutas no incorpora la percepción de los "
  "ciudadanos sobre el estado real de las calles en el momento en que se produce un incidente.")

H2("2.2 El caso de Santa Cruz de la Sierra")
P("Santa Cruz de la Sierra es el municipio más poblado de Bolivia, con 1.606.671 habitantes según los resultados del Censo de "
  "Población y Vivienda 2024; el departamento suma 3.115.386 habitantes (El País, 2024). Su crecimiento se refleja en el parque "
  "automotor, que se resume en la Tabla 1.")
tabla(["Año", "Vehículos en el departamento de Santa Cruz", "Participación en el total nacional"],
      [["2022", "873.478", "35,0 %"], ["2023", "885.380", "35,8 %"], ["2025", "973.537", "36,4 %"],
       ["Variación 2022–2025", "+100.059 (+11,5 %)", "+1,4 puntos"]],
      [3.5, 6.5, 5.5], "Parque automotor del departamento de Santa Cruz",
      "Datos del INE con base en el RUAT, publicados por Los Tiempos (2024) y eju.tv (2026a). La variación es cálculo propio.")
P("La ciudad tiene una estructura urbana radio-concéntrica: alrededor del casco viejo y la Plaza 24 de Septiembre se "
  "desarrollan anillos de circunvalación (del primero al cuarto en la zona consolidada, y otros más hacia la periferia), "
  "conectados por avenidas radiales como la Av. Cristo Redentor, la Av. Grigotá, la Av. Virgen de Cotoca, la Av. Alemana, la Av. "
  "Santos Dumont o la Av. Roca y Coronado. En este esquema, los viajes entre zonas convergen en pocos corredores y en las "
  "intersecciones entre anillos y radiales, de modo que un accidente o un bloqueo en un tramo puede obligar a desvíos de "
  "varios kilómetros. Esta forma de red es, precisamente, la que mejor se representa con un grafo pesado: cada intersección "
  "anillo–radial es un vértice y cada tramo, una arista cuyo costo cambia con las condiciones del tráfico.")
P("Además, la congestión no se queda en el punto del incidente. Cuando un tramo de un anillo se satura, la cola de vehículos "
  "se extiende hacia atrás y alcanza las intersecciones anteriores. Los conductores que buscan desvíos cargan las radiales y "
  "los anillos vecinos, de modo que el atasco se desborda hacia las calles adyacentes. Representar este efecto de desborde "
  "exige propagar la información del reporte a los vértices cercanos del grafo, que es la función del recorrido en anchura "
  "(BFS) del objetivo específico 4.")
P("A la fecha de este informe no se identificó una fuente abierta que permita a los ciudadanos consultar, por calle y hora, el "
  "historial de incidentes viales de la ciudad. TrafficLive busca llenar ese vacío con datos aportados por la propia comunidad.")

H2("2.3 Formulación del problema")
P("¿De qué manera la implementación de Árboles B+ y Grafos Pesados en una aplicación colaborativa puede mejorar la gestión de "
  "reportes de tráfico y el cálculo de rutas óptimas en tiempo real en Santa Cruz de la Sierra, a partir de la "
  "participación ciudadana?", sangria=False)

H2("2.4 Hipótesis")
P("**Hipótesis general (Hi):** la integración de un Árbol B+ para la indexación temporal de los reportes y de un Grafo Pesado "
  "dinámico con el algoritmo A* reduce el tiempo de consulta por rango a un orden O(log n + k) y permite recalcular rutas en "
  "tiempo real ante nuevos reportes ciudadanos, en comparación con una estructura lineal y una búsqueda no informada.",
  sangria=False)
P("**Hipótesis específicas** (los umbrales se fijaron antes de realizar las mediciones):", sangria=False)
viñetas([
    "**H1:** con n = 100.000 reportes, el tiempo promedio de una consulta por rango en el Árbol B+ es al menos 10 veces menor "
    "que en una lista enlazada.",
    "**H2:** en grafos de 1.000 o más intersecciones, A* obtiene rutas de igual costo que Dijkstra expandiendo al menos un 30 % "
    "menos de nodos.",
    "**H3:** el recálculo de la ruta después de un reporte tarda menos de 100 ms en el peor caso, en grafos de hasta 10.000 "
    "intersecciones. Este umbral corresponde al límite en que una respuesta se percibe como instantánea (Nielsen, 1993).",
])
P("**Hipótesis nula (H0):** el uso del Árbol B+ y de A* no produce diferencias relevantes en los tiempos de consulta, en el "
  "trabajo de búsqueda ni en el tiempo de recálculo respecto de la lista enlazada y de Dijkstra.", sangria=False)

H2("2.5 Justificación")
viñetas([
    "**Técnica:** demuestra con mediciones propias por qué un Árbol B+ y un grafo pesado son las estructuras adecuadas para "
    "consultar historiales temporales y recalcular rutas, frente a alternativas lineales.",
    "**Social:** da a los ciudadanos una herramienta para compartir y verificar incidentes, y un historial que puede apoyar "
    "decisiones de movilidad de la población y del municipio.",
    "**Económica:** utiliza software libre (OpenStreetMap, Leaflet) y alojamiento gratuito, por lo que su costo de operación "
    "inicial es prácticamente nulo.",
    "**Académica:** integra en un problema real los contenidos de la asignatura: árboles balanceados, grafos, caminos mínimos, "
    "recorridos y análisis de complejidad.",
])

H2("2.6 Alcances y limitaciones")
viñetas([
    "El Árbol B+ y el grafo se implementan desde cero y se evalúan en memoria principal; no se mide el acceso a disco.",
    "Los experimentos de escalabilidad usan datos sintéticos reproducibles: reportes con coordenadas dentro del área urbana "
    "de Santa Cruz y grafos en cuadrícula. Los algoritmos de rutas se validan además sobre la red vial principal real de la "
    "ciudad (OpenStreetMap), que también usa la demostración web; las calles locales quedan fuera del modelo.",
    "La integración con Waze for Cities depende de un convenio con el Gobierno Autónomo Municipal de Santa Cruz de la Sierra "
    "(GAMSCS); en esta etapa se plantea como trabajo futuro.",
    "La precisión del mapa depende de que exista una masa crítica de usuarios que reporten y validen los incidentes.",
])

# ======================================================================== 3. OBJETIVOS
H1("3. Objetivos")
H2("3.1 Objetivo general")
P("Desarrollar una aplicación web colaborativa denominada TrafficLive que utilice Árboles B+ para la gestión eficiente del "
  "historial de reportes de tráfico y Grafos Pesados para la actualización dinámica de un mapa de congestión en tiempo real "
  "de Santa Cruz de la Sierra, integrando reportes comunitarios con imágenes geolocalizadas.")
H2("3.2 Objetivos específicos")
numerada([
    "Implementar una estructura de Árbol B+ con doble indexación (por identificador y por marca temporal) para el "
    "almacenamiento y la búsqueda eficiente de reportes de tráfico, tanto exacta como por rango de tiempo.",
    "Modelar la red vial como un Grafo Pesado dirigido, cuyos pesos se actualicen dinámicamente según los reportes de los usuarios.",
    "Implementar los algoritmos de Dijkstra y A* para el cálculo de rutas óptimas que se recalculen automáticamente ante "
    "nuevos reportes.",
    "Desarrollar un mapa de calor que visualice los niveles de congestión, usando BFS para propagar la información a los nodos vecinos.",
    "Diseñar un módulo de carga de imágenes con compresión en el cliente que guarde en el Árbol B+ solo la URL de la imagen.",
    "Implementar un sistema de validación comunitaria (votos positivos y negativos) que detecte reportes falsos y ajuste los "
    "pesos del grafo.",
    "Evaluar el rendimiento del Árbol B+ frente a una lista enlazada y de A* frente a Dijkstra, midiendo tiempos de inserción, "
    "consulta y recálculo.",
])
P("La Tabla 2 relaciona cada objetivo con su entregable verificable, el indicador con que se mide y la sección donde se "
  "reporta el resultado, como recomendó la tutoría.")
tabla(["OE", "Entregable", "Indicador medible", "Resultado"],
      [["1", "Módulo arbol_bplus.py y dos índices: por id y por (timestamp, id)", "Tiempo por consulta (µs); 100 % de pruebas de corrección superadas", "8.2, 8.3, Anexo B"],
       ["2", "Módulo grafo_trafico.py con aplicar_reporte()", "Peso de la arista antes y después del reporte", "6.3, 8.2"],
       ["3", "Métodos dijkstra() y a_estrella()", "Costo de ruta idéntico; nodos expandidos; tiempo de recálculo (ms)", "8.4 a 8.6"],
       ["4", "Método propagar_congestion() y capa de calor en la web", "Tiempo de propagación (ms); nodos afectados por nivel", "7.6, 8.4"],
       ["5", "Compresión de imágenes con Canvas en el prototipo", "Tamaño de la imagen antes y después (KB); reducción (%)", "6.4, 8.7"],
       ["6", "Reglas de confianza (factor 0 / 1 / 1,5)", "Un reporte desmentido no altera el peso del grafo", "6.4, 8.2"],
       ["7", "benchmark.py, resultados.json y gráficos", "Factor de aceleración (×) y reducción porcentual", "8.3 a 8.8"]],
      [1.0, 5.4, 6.0, 2.6], "Matriz de objetivos específicos, entregables e indicadores", tam=9.5)

# ======================================================================== 4. MARCO TEÓRICO
H1("4. Marco teórico")
H2("4.1 Conceptos fundamentales")
H3("4.1.1 Estructura de datos")
P("Una estructura de datos es una forma organizada de almacenar información para acceder a ella y modificarla de manera "
  "eficiente. Se clasifican en lineales (arreglos, listas, pilas y colas) y no lineales (árboles y grafos); su elección "
  "determina la complejidad de las operaciones de un sistema (Cormen et al., 2009).")
H3("4.1.2 Árbol B+")
P("El Árbol B+ es una variante del Árbol B (Bayer y McCreight, 1972) diseñada para índices (Comer, 1979). Es un árbol de "
  "búsqueda multivía y balanceado, de orden M, con estas propiedades:")
viñetas([
    "Todos los datos (o punteros a ellos) se almacenan en las hojas, y todas las hojas están al mismo nivel.",
    "Los nodos internos solo contienen claves que guían la búsqueda; cada nodo tiene como máximo M hijos y M − 1 claves, y "
    "cada nodo distinto de la raíz contiene al menos ⌈M/2⌉ − 1 claves.",
    "Las hojas están enlazadas entre sí en orden, lo que permite recorridos secuenciales sin volver a subir por el árbol.",
    "La altura es O(log n) —en base M—, por lo que la inserción, la búsqueda y la eliminación cuestan O(log n), y una consulta por rango "
    "que devuelve k resultados cuesta O(log n + k).",
])
P("La Figura 1 ilustra el índice temporal de TrafficLive: para obtener los reportes entre las 07:10 y las 07:45, la búsqueda "
  "baja una sola vez desde la raíz hasta la hoja que contiene 07:10 y luego avanza por los enlaces entre hojas hasta superar "
  "las 07:45.")
figura("fig_bplus_hojas.png", "Árbol B+ de orden M = 5 con hojas enlazadas y recorrido de una consulta por rango", 16)
H3("4.1.3 Grafo")
P("Un grafo G = (V, E) está formado por un conjunto de vértices V y un conjunto de aristas E que conectan pares de vértices. "
  "Si las aristas tienen dirección, el grafo es dirigido, lo que permite representar calles de un solo sentido.")
H3("4.1.4 Grafo pesado")
P("Un grafo pesado asocia a cada arista (u, v) un valor numérico w(u, v), su peso, que representa un costo, una distancia o un "
  "tiempo. En TrafficLive el peso es el tiempo estimado de viaje en minutos y cambia con los reportes de los usuarios.")
H3("4.1.5 Algoritmo de Dijkstra")
P("Encuentra el camino de costo mínimo desde un vértice origen hacia los demás vértices en un grafo con pesos no negativos "
  "(Dijkstra, 1959). Extrae en cada paso el vértice no visitado con menor distancia acumulada. Su complejidad es O(V²) con una "
  "matriz de adyacencia, O((V + E) log V) con una cola de prioridad implementada como montículo binario —la versión usada en "
  "este proyecto— y O(E + V log V) con un montículo de Fibonacci (Cormen et al., 2009).")
H3("4.1.6 Algoritmo A*")
P("Es un algoritmo de búsqueda informada que ordena la exploración según f(n) = g(n) + h(n), donde g(n) es el costo real "
  "desde el origen y h(n) una estimación del costo restante hasta el destino (Hart et al., 1968). Si la heurística es "
  "admisible —nunca sobreestima el costo real—, A* garantiza encontrar la ruta óptima explorando menos nodos que Dijkstra. En "
  "TrafficLive, h(n) es la distancia en línea recta dividida entre la velocidad máxima permitida, por lo que es admisible.")
H3("4.1.7 Búsqueda en anchura (BFS)")
P("Recorre un grafo por niveles: visita todos los vecinos de un vértice antes de pasar al siguiente nivel, con complejidad "
  "O(V + E). Se usa para hallar caminos mínimos en grafos no pesados y, en este proyecto, para propagar el nivel de congestión "
  "desde la calle reportada hacia sus vecinas, con una intensidad que se reduce a la mitad en cada nivel.")

H2("4.2 ¿Por qué usar Árboles B+ para el almacenamiento de reportes?")
P("Un BST no balanceado puede degenerar en una lista con altura n, y aunque un árbol balanceado (AVL o rojo-negro) logra "
  "O(log n + k) en una consulta por rango, debe recorrer el árbol en inorden subiendo y bajando por los nodos. El Árbol B+ "
  "llega a la primera hoja en O(log n) y luego avanza en forma secuencial por las hojas enlazadas; además, su alto factor de "
  "ramificación reduce la altura y, con ella, los accesos a disco cuando el índice no cabe en memoria.")
tabla(["Criterio", "Lista enlazada", "BST no balanceado", "Árbol B+"],
      [["Búsqueda por ID", "O(n)", "O(log n) prom. / O(n) peor", "O(log n)"],
       ["Búsqueda por rango", "O(n)", "O(n) en el peor caso", "O(log n + k)"],
       ["Inserción", "O(1)", "O(log n) prom. / O(n) peor", "O(log n)"],
       ["Eliminación", "O(n)", "O(log n) prom. / O(n) peor", "O(log n)"],
       ["Recorrido ordenado", "O(n log n) (requiere ordenar)", "O(n)", "O(n) por las hojas"],
       ["Uso en disco", "Malo", "Regular", "Excelente"]],
      [3.8, 3.5, 4.4, 3.6], "Comparación de complejidad para la gestión de reportes",
      "n = número de reportes; k = número de reportes que cumplen la consulta. Basado en Cormen et al. (2009) y Comer (1979).")

H2("4.3 ¿Por qué usar Grafos Pesados para el mapa de tráfico?")
viñetas([
    "Representan naturalmente una red vial: las intersecciones son vértices y los tramos de calle, aristas.",
    "Permiten asignar pesos dinámicos (tiempo de viaje) que cambian con cada reporte sin reconstruir la estructura.",
    "Los algoritmos de caminos mínimos (Dijkstra y A*) operan directamente sobre ellos.",
    "Un grafo dirigido modela restricciones reales: calles de un solo sentido, giros prohibidos o tramos bloqueados (peso infinito).",
])

H2("4.4 Comparación ampliada de estructuras")
tabla(["Estructura", "Búsqueda exacta", "Consulta por rango", "Datos ordenados", "Uso en TrafficLive"],
      [["Arreglo ordenado", "O(log n)", "O(log n + k)", "Sí", "No: insertar cuesta O(n)"],
       ["Lista enlazada", "O(n)", "O(n)", "No", "Línea base del experimento"],
       ["Tabla hash", "O(1) promedio", "O(n)", "No", "No permite rangos de tiempo"],
       ["Árbol AVL", "O(log n)", "O(log n + k)", "Sí", "Altura mayor; más accesos"],
       ["Árbol B", "O(log n)", "O(log n + k)", "Sí", "Datos también en nodos internos"],
       ["Árbol B+", "O(log n)", "O(log n + k)", "Sí, hojas enlazadas", "Índice de reportes (elegido)"],
       ["Matriz de adyacencia", "Arista: O(1)", "Vecinos: O(V)", "—", "No: memoria O(V²)"],
       ["Lista de adyacencia", "Arista: O(grado)", "Vecinos: O(grado)", "—", "Grafo vial (elegido)"]],
      [3.3, 2.6, 2.8, 2.6, 4.0], "Comparación ampliada de estructuras candidatas", tam=9.5)

H2("4.5 Complejidad algorítmica de las operaciones principales")
tabla(["Operación", "Estructura", "Complejidad"],
      [["Insertar reporte", "Árbol B+", "O(log n)"],
       ["Buscar reporte por ID", "Árbol B+", "O(log n)"],
       ["Buscar reportes por rango de tiempo", "Árbol B+", "O(log n + k)"],
       ["Actualizar peso de una arista", "Grafo (lista de adyacencia)", "O(grado del vértice)"],
       ["Calcular ruta más corta", "Grafo pesado (Dijkstra)", "O((V + E) log V)"],
       ["Calcular ruta más corta", "Grafo pesado (A*)", "O((V + E) log V) peor caso; menos nodos con h(n) admisible"],
       ["Propagar congestión a d niveles", "Grafo (BFS)", "O(V + E); en la práctica, solo los vecinos hasta el nivel d"]],
      [5.6, 4.6, 5.3], "Complejidad de las operaciones de TrafficLive")

# ======================================================================== 5. MARCO METODOLÓGICO
H1("5. Marco metodológico")
H2("5.1 Tipo y enfoque de investigación")
P("Se trata de una **investigación aplicada de desarrollo tecnológico**, porque usa conocimientos teóricos (estructuras de datos "
  "y algoritmos de grafos) para construir una solución a un problema concreto de movilidad urbana. El enfoque es "
  "**cuantitativo**: las hipótesis se contrastan con mediciones numéricas de tiempo y de trabajo computacional. El nivel es "
  "**explicativo**, porque busca establecer el efecto de la estructura de datos elegida sobre el rendimiento del sistema "
  "(Hernández Sampieri y Mendoza, 2018).")
H2("5.2 Diseño de investigación")
P("Se aplica un **diseño experimental computacional (benchmarking)** con grupo de control. Para cada tamaño de entrada se "
  "ejecutan exactamente las mismas operaciones sobre la estructura propuesta (Árbol B+, A*) y sobre la estructura de control "
  "(lista enlazada, Dijkstra), con los mismos datos y la misma semilla aleatoria, y se comparan los resultados.")
H2("5.3 Variables e indicadores")
tabla(["Tipo", "Variable", "Indicador / valores", "Unidad"],
      [["Independiente", "Estructura de indexación", "Lista enlazada (control) / Árbol B+ de orden 5", "—"],
       ["Independiente", "Algoritmo de ruta", "Dijkstra (control) / A*", "—"],
       ["Independiente", "Tamaño de la entrada", "1.000 a 100.000 reportes; 100 a 10.000 intersecciones; red real de 3.517", "elementos"],
       ["Dependiente", "Tiempo de búsqueda por ID", "Promedio de 200 consultas", "µs"],
       ["Dependiente", "Tiempo de consulta por rango", "Promedio de 200 consultas de 1 hora", "µs"],
       ["Dependiente", "Tiempo de cálculo de ruta", "Promedio de 40 pares origen–destino", "ms"],
       ["Dependiente", "Trabajo de búsqueda", "Nodos expandidos por ruta", "nodos"],
       ["Dependiente", "Tiempo de recálculo", "Reporte de accidente + nuevo A* (promedio y máximo)", "ms"],
       ["Dependiente", "Tamaño de la imagen", "KB antes y después de comprimir; reducción", "KB, %"],
       ["Controlada", "Entorno de ejecución", "Mismo equipo, lenguaje, semilla y consultas", "—"]],
      [2.6, 4.0, 6.6, 2.0], "Operacionalización de variables", tam=9.5)
H2("5.4 Población y muestra")
P("La **población** está formada por los reportes de incidentes viales y las intersecciones de la red vial urbana de Santa "
  "Cruz de la Sierra. Como aún no existe un historial real de reportes, la **muestra** combina datos sintéticos "
  "reproducibles con datos reales de la ciudad:")
viñetas([
    "Cinco conjuntos de 1.000, 5.000, 10.000, 50.000 y 100.000 reportes, con coordenadas aleatorias dentro del área urbana "
    "(latitud −17,78 ± 0,06; longitud −63,18 ± 0,06), marcas de tiempo distribuidas en 30 días y seis tipos de incidente.",
    "Seis grafos de 100 a 10.000 intersecciones en cuadrícula, que imitan el damero del centro cruceño (cuadras de unos 110 m), "
    "con avenidas rápidas cada cinco cuadras (35–50 km/h) y calles locales más lentas (15–30 km/h).",
    f"La red vial principal real de Santa Cruz (autopistas, troncales, primarias, secundarias y terciarias), descargada de "
    f"OpenStreetMap con la API Overpass (Colaboradores de OpenStreetMap, 2026): {es(OSM['nodos'], 0)} intersecciones y "
    f"{es(OSM['aristas_dirigidas'], 0)} aristas dirigidas; se midieron {OSM['rutas']} rutas aleatorias.",
    "Cinco fotografías reales de avenidas cruceñas (Av. Piraí, Cuarto Anillo y Av. Grigotá, y rotondas del Tercer Anillo), "
    "de 2,6 a 4,2 MB, tomadas con celular y publicadas con licencia libre en Wikimedia Commons (s.f.).",
])
H2("5.5 Técnicas e instrumentos")
viñetas([
    "**Medición de tiempo:** función time.perf_counter() de Python, de alta resolución, promediando varias repeticiones.",
    "**Pruebas de corrección (oráculo):** el Árbol B+ se compara contra un diccionario de Python en 20.000 operaciones aleatorias "
    "de inserción y eliminación con órdenes M = 3, 4, 5, 8 y 32; A* se compara contra Dijkstra en todas las rutas medidas.",
    "**Instrumentos de software:** scripts benchmark.py y pruebas_correccion.py (Anexo D), cuyos resultados se guardan en "
    "resultados.json y se grafican con matplotlib. El script red_osm.py construye el grafo dirigido de la red real y mide "
    "Dijkstra y A* con la misma metodología.",
    "**Medición de la compresión:** la página medir_compresion.html ejecuta, en el navegador Microsoft Edge controlado con "
    "Puppeteer, exactamente el mismo código JavaScript del prototipo (lado mayor de 800 px y JPEG con calidad 0,7).",
    f"**Entorno:** procesador Intel Core i5-1035G1, 24 GB de RAM, Windows 11 y Python {RES['python']}.",
])
H2("5.6 Procedimiento")
numerada([
    "Implementar desde cero el Árbol B+ y el grafo pesado con Dijkstra, A* y BFS.",
    "Verificar la corrección de las implementaciones con las pruebas de oráculo.",
    "Generar los conjuntos de datos con semilla fija (2026).",
    "Ejecutar las mediciones para cada tamaño de entrada sobre la estructura propuesta y la de control.",
    "Registrar los resultados en resultados.json y elaborar tablas y gráficos.",
    "Contrastar cada hipótesis con su criterio de aceptación.",
])
H2("5.7 Criterios de contraste de hipótesis")
tabla(["Hipótesis", "Indicador", "Criterio de aceptación"],
      [["H1", "Aceleración en consulta por rango con n = 100.000", "≥ 10 veces"],
       ["H2", "Reducción de nodos expandidos de A* frente a Dijkstra (≥ 1.000 nodos) y costo de ruta", "≥ 30 % y costo idéntico"],
       ["H3", "Tiempo máximo de recálculo con 10.000 intersecciones", "< 100 ms"]],
      [2.2, 8.8, 4.5], "Criterios de aceptación definidos antes de la experimentación")
H2("5.8 Matriz de consistencia")
tabla(["Problema", "Objetivo general", "Hipótesis general", "Variables", "Metodología"],
      [["¿De qué manera la implementación de Árboles B+ y Grafos Pesados en una aplicación colaborativa puede mejorar la gestión "
        "de reportes de tráfico y el cálculo de rutas óptimas en tiempo real en Santa Cruz de la Sierra?",
        "Desarrollar TrafficLive con Árboles B+ para el historial de reportes y Grafos Pesados para un mapa de congestión "
        "dinámico con reportes comunitarios geolocalizados.",
        "El Árbol B+ y el grafo dinámico con A* reducen la consulta por rango a O(log n + k) y permiten recalcular rutas en tiempo "
        "real frente a una estructura lineal y una búsqueda no informada.",
        "VI: estructura de datos, algoritmo, tamaño de entrada. VD: tiempos de búsqueda, rango, ruta y recálculo; nodos expandidos.",
        "Investigación aplicada, cuantitativa, explicativa. Diseño experimental computacional con grupo de control. Muestra "
        "sintética reproducible."]],
      [3.3, 3.0, 3.3, 2.9, 3.0], "Matriz de consistencia de la investigación", tam=8.5, alinear_num=False)

# ======================================================================== 6. PROPUESTA
H1("6. Propuesta de solución")
H2("6.1 Descripción general del sistema TrafficLive")
P("TrafficLive es una aplicación web formada por tres módulos que trabajan en cadena: cuando un ciudadano envía un reporte, este "
  "se indexa en el Árbol B+, se ubica la arista del grafo más cercana a sus coordenadas, se incrementa su peso, A* recalcula las "
  "rutas afectadas y BFS actualiza el mapa de calor.")
numerada([
    "**Módulo de reportes (Árbol B+):** almacena y consulta los reportes por identificador y por rango de tiempo.",
    "**Módulo de mapa en vivo (Grafo Pesado):** visualiza la congestión y calcula rutas óptimas.",
    "**Módulo de imágenes y validación comunitaria:** comprime y almacena las fotos y gestiona los votos de confianza.",
])
H2("6.2 Módulo de almacenamiento y búsqueda de reportes (Árbol B+)")
tabla(["Campo", "Tipo", "Descripción"],
      [["id", "entero", "Identificador único del reporte"],
       ["latitud, longitud", "real", "Ubicación del incidente (GPS del dispositivo)"],
       ["timestamp", "fecha y hora", "Momento del reporte"],
       ["tipo_incidente", "texto", "atasco leve, moderado o severo; accidente; bache; inundación; bloqueo"],
       ["url_imagen", "texto", "Dirección de la foto en el almacenamiento externo"],
       ["votos_positivos, votos_negativos", "entero", "Validación de la comunidad"],
       ["estado", "texto", "activo o archivado"]],
      [4.6, 2.6, 8.3], "Estructura de un reporte")
viñetas([
    "**Orden:** M = 5 (configurable), es decir, hasta 4 claves y 5 hijos por nodo.",
    "**Doble indexación:** un Árbol B+ ordena sus datos por una única clave; por eso se mantienen dos instancias que "
    "apuntan a los mismos reportes.",
    "**Índice por identificador:** clave = id, para búsquedas exactas.",
    "**Índice temporal:** clave compuesta (timestamp, id), que mantiene el orden por hora sin conflictos entre reportes "
    "simultáneos y permite consultas como «todos los reportes entre las 07:00 y las 08:00».",
    "**Operaciones:** insertar(reporte), buscar(id), buscar_rango(inicio, fin) y eliminar(id), con división (split), "
    "préstamo y fusión de nodos para mantener el balance.",
])
H2("6.3 Módulo del mapa en vivo y cálculo de rutas (Grafo Pesado)")
P(f"La red vial se modela como un grafo dirigido G = (V, E): V son las intersecciones, E los tramos de calle, y el peso de "
  f"cada arista es el tiempo de viaje en minutos (longitud del tramo dividida entre la velocidad esperada). Cuando llega un "
  f"reporte, se busca la arista más cercana a sus coordenadas y su peso aumenta según el tipo de incidente (Tabla {n_tab + 1}).")
tabla(["Tipo de incidente", "Incremento del peso"],
      [["Atasco leve", "+2 min"], ["Atasco moderado", "+5 min"], ["Atasco severo", "+10 min"], ["Accidente", "+15 min"],
       ["Calle bloqueada", "peso = ∞ (la arista queda fuera de cualquier ruta)"]],
      [6, 8], "Penalización del peso de una arista según el tipo de incidente")
viñetas([
    "**Dijkstra:** ruta de menor tiempo entre origen y destino; se usa como referencia.",
    "**A*:** misma ruta óptima con menos exploración, gracias a la heurística h(n) = distancia en línea recta / velocidad máxima.",
    "**BFS:** propaga la congestión desde el tramo reportado: intensidad 1 en sus extremos, 0,5 en los vecinos y 0,25 en el "
    "segundo nivel, para construir el mapa de calor.",
    "**Sentido del reporte:** como el grafo es dirigido, aplicar_reporte() penaliza por defecto solo la arista del sentido "
    "reportado (un carril de una avenida con carriles separados). Con el parámetro bidireccional=True penaliza también el "
    "sentido contrario, por ejemplo cuando una calle queda bloqueada de lado a lado.",
])
H2("6.4 Módulo de imágenes y validación comunitaria")
P("Flujo de carga de imágenes:", sangria=False)
numerada([
    "El usuario toma una foto desde su dispositivo móvil.",
    "La imagen se redimensiona (lado mayor de 800 px) y se comprime a JPEG con calidad 0,7 en el navegador, mediante la API Canvas.",
    "En la arquitectura de producción, la imagen comprimida se sube a un servicio de almacenamiento (Firebase Storage o AWS S3).",
    "El servicio devuelve una URL, que se guarda en el Árbol B+ junto con los metadatos del reporte; la imagen no se almacena en el índice.",
])
P("En el prototipo web actual, que funciona por completo en el navegador, todavía no hay servidor ni almacenamiento en la "
  "nube (Tabla 11). La imagen comprimida se conserva en la memoria del cliente y el reporte guarda esa referencia local. La "
  "subida a Firebase Storage y el uso de su URL corresponden a la siguiente fase, junto con la API en Flask.")
P("Reglas de validación comunitaria (se aplican cuando un reporte acumula al menos 3 votos):", sangria=False)
viñetas([
    "Si más del 70 % de los votos son negativos, el reporte se marca como «no verificado» y su impacto en el grafo se reduce a cero.",
    "Si más del 70 % de los votos son positivos, su penalización en el grafo se multiplica por 1,5 (aumenta un 50 %).",
    "En cualquier otro caso, el reporte conserva su penalización normal (factor 1).",
])
H2("6.5 Validación cruzada con fuentes externas de tráfico")
viñetas([
    "**Waze for Cities:** el programa intercambia datos de tráfico con entidades públicas mediante convenio. Se propone gestionar "
    "el acceso a través del GAMSCS: si Waze también reporta congestión en la calle, el reporte sube su nivel de confianza; si "
    "reporta flujo normal, se marca para revisión. En el prototipo actual solo se usan datos comunitarios.",
    "**Google Maps TrafficLayer:** puede mostrarse como capa visual de contexto, pero sus datos no son accesibles por "
    "programación, por lo que no intervienen en los pesos del grafo.",
    "**Privacidad:** se eliminan de las fotos los metadatos distintos de la ubicación, no se publica la identidad de quien "
    "reporta y solo se conservan datos agregados en el historial.",
])

# ======================================================================== 7. DESARROLLO
H1("7. Desarrollo e implementación")
H2("7.1 Arquitectura del sistema")
P("La Figura 2 muestra la arquitectura objetivo. El cliente web envía los reportes por HTTPS a una API que mantiene en memoria el "
  "Árbol B+ y el grafo, persiste los datos crudos en una base de datos y guarda las imágenes en un almacenamiento externo. El "
  "prototipo actual ejecuta la misma lógica en el navegador (versión JavaScript de las estructuras), lo que permite usarlo sin "
  "servidor durante la feria.")
figura("fig_arquitectura.png", "Arquitectura de TrafficLive", 16)
H2("7.2 Tecnologías utilizadas")
tabla(["Componente", "Tecnología", "Estado"],
      [["Núcleo de estructuras y experimentos", f"Python {RES['python']} (sin bibliotecas de estructuras)", "Implementado"],
       ["Prototipo web", "HTML, CSS y JavaScript", "Implementado y publicado"],
       ["Mapa base", "Leaflet 1.9.4 + OpenStreetMap", "Implementado"],
       ["Red vial real", "OpenStreetMap (API Overpass, licencia ODbL)", "Implementado"],
       ["Mapa de calor", "Leaflet.heat 0.2.0", "Implementado"],
       ["Gráficos de resultados", "matplotlib (informe) y Chart.js 4.4.1 (web)", "Implementado"],
       ["Alojamiento del prototipo", "Vercel (capa gratuita)", "Publicado"],
       ["API del servidor", "Python / Flask", "Siguiente fase"],
       ["Base de datos", "SQLite o PostgreSQL", "Siguiente fase"],
       ["Almacenamiento de imágenes", "Firebase Storage (capa gratuita)", "Siguiente fase"],
       ["Control de versiones", "Git + GitHub", "En uso"]],
      [5.2, 6.5, 3.8], "Tecnologías del proyecto")
H2("7.3 Implementación del Árbol B+")
P("**El Árbol B+ fue implementado desde cero por el equipo**, sin bibliotecas externas, tal como recomienda la asignatura. La "
  "clase NodoBPlus guarda las claves, los hijos (o los valores, si es hoja) y el enlace a la hoja siguiente; la clase ArbolBPlus "
  "implementa la inserción con división de nodos, la búsqueda exacta, la búsqueda por rango sobre las hojas enlazadas y la "
  "eliminación con préstamo y fusión. El siguiente fragmento muestra la búsqueda por rango; el código completo está en el Anexo B.")
codigo('''def buscar_rango(self, inicio, fin):
    """Devuelve los valores con inicio <= clave <= fin: O(log n + k)."""
    resultado = []
    hoja = self._buscar_hoja(inicio)            # 1) baja una sola vez: O(log n)
    i = bisect_left(hoja.claves, inicio)
    while hoja is not None:                     # 2) recorre hojas enlazadas: O(k)
        while i < len(hoja.claves):
            if hoja.claves[i] > fin:
                return resultado
            resultado.append(hoja.hijos[i])
            i += 1
        hoja, i = hoja.siguiente, 0
    return resultado''')
P("Al insertar, si una hoja supera M − 1 claves se divide en dos: la primera clave de la nueva hoja se copia al padre y se "
  "actualizan los enlaces. Si el padre también se desborda, se divide y su clave central sube (sin copiarse). Cuando se divide "
  "la raíz, el árbol crece un nivel, lo que mantiene todas las hojas a la misma profundidad.")
H2("7.4 Implementación del Grafo Pesado")
P("**El grafo también se implementó desde cero**, como listas de adyacencia (diccionario u → {v: peso}). La primera versión del "
  "informe proponía NetworkX; se reemplazó por una implementación propia para aplicar directamente los contenidos de la materia "
  "y poder medir los nodos expandidos. La cola de prioridad de Dijkstra y A* es un montículo binario (módulo heapq de la "
  "biblioteca estándar).")
codigo('''def a_estrella(self, origen, destino):
    g = {origen: 0.0}; previo = {}; cerrado = set()
    heap = [(self.heuristica(origen, destino), 0.0, origen)]
    while heap:
        _, gu, u = heapq.heappop(heap)
        if u in cerrado:
            continue
        cerrado.add(u)
        if u == destino:
            break
        for v, w in self.ady[u].items():
            ng = gu + w
            if ng < g.get(v, inf):
                g[v] = ng; previo[v] = u
                heapq.heappush(heap, (ng + self.heuristica(v, destino), ng, v))
    return self._reconstruir(previo, origen, destino), g.get(destino, inf)''')
H2("7.5 Integración con la API de mapas")
viñetas([
    "**Leaflet.js** dibuja el mapa base de OpenStreetMap, centrado en la Plaza 24 de Septiembre.",
    "**Polilíneas** (L.polyline) representan cada tramo del grafo, coloreado según la relación entre su peso actual y su peso base.",
    "**Capa de calor** (biblioteca libre Leaflet.heat) muestra la intensidad propagada por BFS en cada intersección.",
    "**Red real:** el archivo red_santa_cruz.json, generado por red_osm.py, contiene las intersecciones y los tramos con su "
    "sentido de circulación; el navegador construye con él el grafo dirigido.",
    "**Marcadores** (L.marker) indican el origen y el destino; la ruta de A* se dibuja en azul y la ruta anterior, punteada.",
])
H2("7.6 Interfaz de usuario")
P(f"El prototipo está publicado en **{URL_WEB}**, con su código en https://github.com/Kato-001/TrafficLive, y "
  "tiene estas secciones principales:", sangria=False)
viñetas([
    "**Inicio:** resume el proyecto y los resultados medidos (Figura 3).",
    "**Demo interactiva:** mapa con la red vial real de Santa Cruz como grafo dirigido. El usuario elige origen y destino, "
    "indica si el incidente afecta uno o ambos sentidos, reporta incidentes "
    "(opcionalmente con foto, que se comprime en el navegador) y vota los reportes de otros. El botón «Modo feria» bloquea un "
    "tramo de la ruta actual y muestra cómo A* la recalcula al instante (Figura 4). Incluye una consulta por rango de horas "
    "sobre un historial simulado de 400 reportes.",
    "**Visualizador del Árbol B+:** permite insertar claves, cambiar el orden M y ejecutar consultas por rango, resaltando el "
    "camino de descenso y las hojas recorridas (Figura 5).",
    "**Resultados:** gráficos interactivos del benchmark, comparación entre la cuadrícula y la red real, tabla de "
    "compresión de fotos y contraste de hipótesis.",
    "**Equipo y descargas:** autores con su carrera e identificador ORCID, el informe en PDF, el repositorio y el logo.",
])
figura("cap_inicio.png", "Pantalla de inicio del prototipo web", 15.5, f"Captura de {URL_WEB}.")
figura("cap_demo_recalculo.png", "Demo interactiva sobre la red real: recálculo de ruta tras bloquear un tramo («Modo feria»)", 15.5,
       "La línea azul es la nueva ruta calculada con A*; la mancha de color es el mapa de calor propagado con BFS desde el "
       "tramo bloqueado.")
figura("cap_arbol_bplus.png", "Visualizador didáctico del Árbol B+", 14, f"Captura de {URL_WEB}.")

# ======================================================================== 8. PRUEBAS Y RESULTADOS
H1("8. Pruebas y resultados")
H2("8.1 Metodología de pruebas")
P("Las pruebas siguieron el diseño descrito en el capítulo 5. A diferencia de la primera presentación, cuyas tablas contenían "
  "valores estimados, **todos los valores de este capítulo fueron medidos** con las implementaciones propias del Anexo B y el "
  "Anexo C, ejecutando benchmark.py con semilla fija; cualquier persona puede reproducirlos. Los tiempos del Árbol B+ y de la "
  "lista se expresan en microsegundos (1 µs = 0,001 ms).")
H2("8.2 Pruebas de corrección")
viñetas([
    "**Árbol B+:** 20.000 operaciones aleatorias de inserción y eliminación por cada orden M ∈ {3, 4, 5, 8, 32}. Tras cada "
    "secuencia se verificó que el recorrido por las hojas devuelve las claves ordenadas, que el tamaño coincide y que todas las "
    "búsquedas exactas y por rango coinciden con el diccionario de referencia. Resultado: 100 % de coincidencia.",
    "**Grafo:** en 100 pares aleatorios y en las 240 rutas del benchmark, A* y Dijkstra devolvieron exactamente el mismo costo. "
    "Al bloquear un tramo de la ruta, la nueva ruta lo evita, y un reporte con factor de confianza 0 no modifica el peso.",
])
H2("8.3 Resultados de rendimiento del Árbol B+")
tabla(["N° de reportes", "Altura", "Inserción B+ (µs)", "Búsqueda por ID: B+ (µs)", "Búsqueda por ID: lista (µs)", "Aceleración"],
      [[es(r["n"], 0), r["altura_bplus"], us(r["insercion_bplus_ms"]), us(r["busqueda_id_bplus_ms"]),
        us(r["busqueda_id_lista_ms"]), "×" + es(r["busqueda_id_lista_ms"] / r["busqueda_id_bplus_ms"], 0)] for r in R],
      [2.4, 1.5, 2.6, 3.0, 3.1, 2.4], "Tiempo promedio de inserción y de búsqueda por identificador", tam=9.5,
      fuente="Inserción: promedio sobre los n reportes (incluye los dos índices del Árbol B+). Búsquedas: promedio de 200 consultas.")
t_id = n_tab
tabla(["N° de reportes", "k promedio", "Rango: Árbol B+ (µs)", "Rango: lista (µs)", "Aceleración"],
      [[es(r["n"], 0), es(r["k_promedio"], 1), us(r["rango_bplus_ms"]), us(r["rango_lista_ms"]),
        "×" + es(r["rango_lista_ms"] / r["rango_bplus_ms"], 0)] for r in R],
      [3.0, 2.5, 3.5, 3.5, 3.0], "Tiempo promedio de una consulta por rango de una hora", tam=9.5,
      fuente="k = número promedio de reportes que devuelve la consulta. La lista enlazada debe revisar los n nodos en cada consulta.")
t_rango = n_tab
figura("fig_busqueda_id.png", "Tiempo de búsqueda por identificador frente al número de reportes", 13.5,
       f"Ambos ejes en escala logarítmica. Elaboración propia con los datos de la Tabla {t_id}.")
figura("fig_busqueda_rango.png", "Tiempo de consulta por rango frente al número de reportes", 13.5,
       f"Ambos ejes en escala logarítmica. Elaboración propia con los datos de la Tabla {t_rango}.")
P(f"Con 100.000 reportes, el Árbol B+ encuentra un reporte por identificador en {us(r100['busqueda_id_bplus_ms'])} µs, mientras "
  f"que la lista enlazada necesita {us(r100['busqueda_id_lista_ms'])} µs: una aceleración de {es(x_id, 0)} veces. En la consulta "
  f"por rango, la aceleración es de {es(x_rango, 0)} veces. La altura del árbol solo pasó de 6 a 9 niveles mientras los datos "
  "se multiplicaban por 100, lo que confirma el crecimiento logarítmico.")
H2("8.4 Resultados de rendimiento del Grafo Pesado")
tabla(["Nodos", "Aristas", "Dijkstra (ms)", "A* (ms)", "Reducción de tiempo", "Nodos exp. Dijkstra", "Nodos exp. A*", "Reducción de nodos"],
      [[es(g["nodos"], 0), es(g["aristas"], 0), es(g["dijkstra_ms"], 2), es(g["a_estrella_ms"], 2),
        es((1 - g["a_estrella_ms"] / g["dijkstra_ms"]) * 100, 0) + " %", es(g["expandidos_dijkstra"], 0),
        es(g["expandidos_a_estrella"], 0), es((1 - g["expandidos_a_estrella"] / g["expandidos_dijkstra"]) * 100, 0) + " %"]
       for g in G],
      [1.6, 1.7, 2.0, 1.7, 2.1, 2.2, 1.9, 2.1], "Cálculo de rutas: Dijkstra frente a A*", tam=9,
      fuente="Promedio de 40 pares origen–destino aleatorios por grafo. En todos los casos ambos algoritmos devolvieron el mismo costo.")
figura("fig_dijkstra_vs_aestrella.png", "Tiempo de cálculo y nodos expandidos de Dijkstra y A*", 16,
       f"Elaboración propia con los datos de la Tabla {n_tab}.")
P(f"A* expande sistemáticamente cerca de la mitad de los nodos que Dijkstra (entre {es(red_exp_min * 100, 0)} % y "
  f"{es(max(1 - g['expandidos_a_estrella'] / g['expandidos_dijkstra'] for g in G) * 100, 0)} % menos) y obtiene la misma ruta "
  f"óptima. La reducción en tiempo es menor ({es(red_t * 100, 0)} % con 10.000 nodos) porque A* calcula la heurística en "
  "cada inserción en la cola de prioridad, lo que en Python tiene un costo apreciable. La propagación de congestión con BFS a "
  f"dos niveles tardó en promedio {es(g10k['bfs_ms'] * 1000, 1)} µs, porque solo visita los vecinos cercanos al tramo reportado.")
H2("8.5 Validación en la red vial real de Santa Cruz")
P("Los grafos en cuadrícula permiten medir la escalabilidad, pero la topología de la ciudad es radio-concéntrica y dirigida. "
  "Por eso las mediciones de rutas se repitieron sobre la red vial principal real, descargada de OpenStreetMap y convertida "
  f"en grafo dirigido por red_osm.py (Figura {n_fig + 1}).")
figura("fig_red_osm.png", "Red vial principal real de Santa Cruz de la Sierra modelada como grafo dirigido", 13,
       f"Elaboración propia con datos de OpenStreetMap. De {es(OSM['tramos'], 0)} tramos, {es(OSM['tramos_sentido_unico'], 0)} son de un "
       "solo sentido, porque los anillos y las avenidas principales tienen carriles separados.")
g10 = G[-1]
tabla(["Indicador", "Cuadrícula sintética", "Red real (OSM)"],
      [["Intersecciones (nodos)", es(g10["nodos"], 0), es(OSM["nodos"], 0)],
       ["Aristas dirigidas", es(g10["aristas"], 0), es(OSM["aristas_dirigidas"], 0)],
       ["Rutas medidas", "40", es(OSM["rutas"], 0)],
       ["Nodos expandidos: Dijkstra / A*", es(g10["expandidos_dijkstra"], 0) + " / " + es(g10["expandidos_a_estrella"], 0),
        es(OSM["expandidos_dijkstra"], 0) + " / " + es(OSM["expandidos_a_estrella"], 0)],
       ["Reducción de nodos con A*", es(red_exp * 100, 1) + " %", es(red_osm * 100, 1) + " %"],
       ["Tiempo: Dijkstra / A* (ms)", es(g10["dijkstra_ms"], 2) + " / " + es(g10["a_estrella_ms"], 2),
        es(OSM["dijkstra_ms"], 2) + " / " + es(OSM["a_estrella_ms"], 2)],
       ["Reducción de tiempo con A*", es(red_t * 100, 1) + " %", es(red_t_osm * 100, 1) + " %"],
       ["Recálculo promedio / máximo (ms)", es(g10["recalculo_ms"], 2) + " / " + es(g10["recalculo_max_ms"], 2),
        es(OSM["recalculo_ms"], 2) + " / " + es(OSM["recalculo_max_ms"], 2)]],
      [6.0, 4.6, 4.6], "Cuadrícula de 10.000 nodos frente a la red vial real", tam=9.5,
      fuente="En la red real, el reporte de accidente penaliza solo el sentido de la ruta (grafo dirigido). En todas las rutas, "
             "A* y Dijkstra devolvieron el mismo costo.")
P(f"En la red real, A* conservó la optimalidad en las {OSM['rutas']} rutas y expandió un {es(red_osm * 100, 1)} % menos de "
  f"nodos, una poda similar a la de la cuadrícula ({es(red_exp * 100, 1)} %). En cambio, la reducción de tiempo fue mayor "
  f"({es(red_t_osm * 100, 1)} % frente a {es(red_t * 100, 1)} %): las vías rápidas de los anillos concentran los caminos "
  "mínimos, y la heurística euclidiana guía antes la búsqueda hacia ellas. El recálculo más lento fue de "
  f"{es(OSM['recalculo_max_ms'], 1)} ms, también muy por debajo del umbral de 100 ms.")
H2("8.6 Recálculo de rutas en tiempo real")
tabla(["Nodos", "Recálculo promedio (ms)", "Recálculo máximo (ms)"],
      [[es(g["nodos"], 0), es(g["recalculo_ms"], 2), es(g["recalculo_max_ms"], 2)] for g in G],
      [4, 5, 5], "Tiempo de recálculo de ruta tras un reporte de accidente",
      "Para 20 rutas por grafo se aplicó un reporte de accidente (+15 min) en un tramo de la ruta y se recalculó con A*.")
figura("fig_recalculo.png", "Tiempo de recálculo de ruta frente al tamaño del grafo", 13.5,
       "Cuadrícula sintética. La línea roja marca el umbral de 100 ms de respuesta inmediata (Nielsen, 1993).")
H2("8.7 Compresión de imágenes en el cliente")
P("Para medir el indicador del objetivo 5 se comprimieron cinco fotografías reales de avenidas cruceñas con el mismo código "
  "del prototipo: lado mayor de 800 px y JPEG con calidad 0,7, en el navegador.")
tabla(["Foto", "Ubicación", "Resolución original", "Original (KB)", "Comprimida (KB)", "Reducción", "Tiempo (ms)"],
      [[str(i), lugar, f["original_px"].replace("x", " × "), es(f["original_kb"], 0), es(f["comprimida_kb"], 1),
        es(f["reduccion_pct"], 1) + " %", es(f["tiempo_ms"], 0)]
       for i, (f, lugar) in enumerate(zip(FOTOS, ["Av. Piraí (3er–4to Anillo)", "4to Anillo y Radial 17½", "4to Anillo y Av. Grigotá",
                                                  "Rotonda 3er Anillo externo", "Rotonda 3er Anillo y Av. San Martín"]), 1)]
      + [["", "**Promedio**", "", "**" + es(foto_orig, 0) + "**", "**" + es(foto_comp, 1) + "**", "**" + es(foto_red, 1) + " %**",
          "**" + es(sum(f["tiempo_ms"] for f in FOTOS) / len(FOTOS), 0) + "**"]],
      [1.0, 4.4, 2.6, 2.2, 2.4, 2.0, 1.8], "Compresión de fotografías reales en el navegador", tam=9,
      fuente="Fotografías de Wikimedia Commons (s.f.). Medición con medir_compresion.html en Microsoft Edge. 1 KB = 1.024 bytes.")
P(f"En promedio, cada fotografía pasó de {es(foto_orig / 1024, 1)} MB a {es(foto_comp, 1)} KB, una reducción del "
  f"{es(foto_red, 1)} %, en unos {es(sum(f['tiempo_ms'] for f in FOTOS) / len(FOTOS), 0)} ms. Con datos móviles, subir una foto "
  "de 58 KB en lugar de una de 3,5 MB hace que el reporte sea casi inmediato, y la resolución de 800 px sigue siendo suficiente "
  "para reconocer el incidente.")
H2("8.8 Contraste de hipótesis")
tabla(["Hipótesis", "Criterio", "Valor medido", "Decisión"],
      [["H1", "≥ 10 veces", f"×{es(x_rango, 0)} con 100.000 reportes", "**Se acepta**"],
       ["H2", "≥ 30 % menos nodos y costo idéntico", f"{es(red_exp_min * 100, 0)} %–{es(red_exp * 100, 0)} % menos (cuadrícula) y {es(red_osm * 100, 1)} % (red real); costo idéntico en 440 rutas", "**Se acepta**"],
       ["H3", "< 100 ms", f"{es(rec_max, 1)} ms (10.000 nodos) y {es(OSM['recalculo_max_ms'], 1)} ms (red real), en el peor caso", "**Se acepta**"]],
      [2.2, 4.4, 6.0, 2.9], "Contraste de las hipótesis específicas")
P("Al aceptarse las tres hipótesis específicas se rechaza la hipótesis nula y se acepta la hipótesis general: el Árbol B+ y el "
  "grafo dinámico con A* producen mejoras relevantes frente a las estructuras de control. Dado que las diferencias son de dos a "
  "tres órdenes de magnitud en el Árbol B+, no dependen de la variación aleatoria entre ejecuciones.")
H2("8.9 Comparación con soluciones tradicionales")
tabla(["Criterio", "Google Maps", "Waze", "TrafficLive"],
      [["Costo para el usuario", "Gratuito", "Gratuito", "Gratuito; software libre y alojamiento gratuito"],
       ["Acceso a los datos de tráfico", "Solo visual (TrafficLayer)", "Mediante convenio (Waze for Cities)", "Historial propio consultable por rango"],
       ["Participación ciudadana", "Reportes en la app, sin historial abierto", "Alta: reportes en la app", "Alta: reportes con foto y votos de confianza"],
       ["Evidencia fotográfica", "No es parte del reporte", "No es parte del reporte", "Sí, comprimida en el cliente"],
       ["Personalización local", "No", "No", "Sí: pesos, reglas y zonas configurables"],
       ["Cobertura y precisión", "Global y alta", "Global y alta", "Depende de la cantidad de usuarios activos"]],
      [3.6, 3.7, 3.7, 4.5], "Comparación cualitativa con soluciones existentes", tam=9.5, alinear_num=False)
P("TrafficLive no busca reemplazar a estas plataformas, sino complementarlas con un historial local abierto, verificable con "
  "imágenes y apoyado en estructuras de datos eficientes. Su principal desventaja es que necesita una comunidad activa para "
  "alcanzar la cobertura de las aplicaciones globales.")
H2("8.10 Análisis de resultados")
viñetas([
    "**El Árbol B+ es la estructura adecuada para el historial:** su ventaja crece con el volumen de datos, porque la lista "
    "enlazada crece en forma lineal y el árbol en forma logarítmica. En la búsqueda por rango, la aceleración es menor que en la "
    "búsqueda por ID porque ambos deben devolver los k reportes encontrados, y k crece con n (138 reportes por hora con 100.000).",
    "**El costo de la inserción es aceptable:** insertar en el Árbol B+ (dos índices) es más lento que agregar al inicio de una "
    f"lista ({us(r100['insercion_bplus_ms'])} µs frente a {us(r100['insercion_lista_ms'])} µs con 100.000 reportes), pero sigue "
    "siendo despreciable frente a la frecuencia real de los reportes, y se compensa ampliamente en cada consulta.",
    "**A* reduce el trabajo a la mitad sin perder optimalidad**, gracias a una heurística admisible. Solo en el grafo más "
    "pequeño (100 nodos) A* resultó un 5 % más lento que Dijkstra: con tan pocos nodos, el costo de calcular la heurística "
    "supera el ahorro de explorar menos. A partir de 400 nodos la ventaja de A* es constante.",
    "**El sistema responde en tiempo real:** incluso el peor recálculo medido es unas seis veces menor que el umbral de 100 ms, "
    "con margen para grafos más grandes o un servidor con más carga.",
    "**La compresión en el cliente cumple su propósito:** reduce las fotos un 98 % sin servidor, lo que mantiene ligero el "
    "reporte y el índice.",
    "**Limitaciones de validez:** los reportes son sintéticos, la red real incluye solo las vías principales y las "
    "mediciones se hicieron en un solo equipo, en un lenguaje interpretado y en memoria principal.",
])

# ======================================================================== CONCLUSIONES
H1("Conclusiones")
numerada([
    f"Se implementó desde cero un Árbol B+ de orden 5 que, con 100.000 reportes, es {es(x_id, 0)} veces más rápido que una lista "
    f"enlazada en la búsqueda por identificador y {es(x_rango, 0)} veces más rápido en la consulta por rango de una hora, "
    "confirmando en la práctica la diferencia entre O(log n + k) y O(n). El costo de la doble indexación es una inserción más "
    f"lenta ({us(r100['insercion_bplus_ms'])} µs frente a {us(r100['insercion_lista_ms'])} µs en la lista), despreciable frente "
    "a la ganancia en cada consulta (objetivos 1 y 7).",
    "El modelado de la red vial como grafo pesado dirigido permitió actualizar dinámicamente los pesos de las calles según el "
    "tipo de incidente reportado, sin reconstruir la estructura (objetivo 2).",
    f"A* obtuvo exactamente las mismas rutas óptimas que Dijkstra en todas las pruebas, expandiendo entre un {es(red_exp_min * 100, 0)} % y un "
    f"{es(red_exp * 100, 0)} % menos de nodos, y el recálculo tras un reporte tardó como máximo {es(rec_max, 1)} ms con 10.000 "
    f"intersecciones y {es(OSM['recalculo_max_ms'], 1)} ms en la red vial real de Santa Cruz, donde A* exploró un "
    f"{es(red_osm * 100, 1)} % menos de nodos; ambos valores están muy por debajo del umbral de 100 ms (objetivo 3).",
    f"La propagación de la congestión con BFS a dos niveles tardó en promedio {es(g10k['bfs_ms'] * 1000, 1)} µs, porque "
    "solo recorre los vecinos del tramo reportado; así el mapa de calor refleja el desborde del atasco hacia las calles "
    "adyacentes (objetivo 4).",
    f"La compresión en el navegador redujo cinco fotografías reales de {es(foto_orig, 0)} KB a {es(foto_comp, 1)} KB en "
    f"promedio (−{es(foto_red, 1)} %), y el Árbol B+ guarda solo la referencia de la imagen, lo que mantiene ligero el índice "
    "(objetivo 5).",
    "Las reglas de validación comunitaria anulan el efecto de los reportes desmentidos y refuerzan los confirmados, lo que reduce "
    "el impacto de los datos falsos sobre las rutas (objetivo 6).",
    "Se aceptaron las tres hipótesis específicas y, con ellas, la hipótesis general: la combinación de estructuras de datos no "
    "lineales con la participación ciudadana es una solución viable y de bajo costo para la gestión del tráfico en Santa Cruz "
    f"de la Sierra. Se cumplió el objetivo general: TrafficLive se desarrolló y se publicó como aplicación web funcional en "
    f"{URL_WEB}, con su código abierto en GitHub.",
])

H1("Recomendaciones")
numerada([
    "Implementar la API en Flask con persistencia en PostgreSQL y almacenamiento de imágenes en Firebase, para pasar del prototipo "
    "en el navegador a un servicio multiusuario.",
    "Ampliar el grafo real con las calles locales de OpenStreetMap y calibrar las velocidades de cada vía con mediciones de "
    "campo en horas pico.",
    "Gestionar con el GAMSCS un convenio con Waze for Cities para la validación cruzada de los reportes.",
    "Realizar una prueba piloto con usuarios reales en uno o dos corredores (por ejemplo, el 2do Anillo y la Av. Cristo Redentor) "
    "para medir la cantidad y la precisión de los reportes.",
    "Repetir el benchmark con al menos 30 ejecuciones independientes y aplicar una prueba estadística pareada (t de Student o "
    "Wilcoxon) para reportar intervalos de confianza.",
    "Evaluar el Árbol B+ almacenado en disco, donde su ventaja frente a otros árboles balanceados es todavía mayor.",
    "Explorar modelos de predicción de atascos a partir del historial almacenado en el Árbol B+.",
    "Para la feria: usar el «Modo feria» de la demo para que el jurado bloquee una calle y vea el recálculo inmediato de A*; "
    "mostrar en el póster la comparación visual entre recorrer una lista elemento por elemento y bajar por el Árbol B+ y avanzar "
    f"por sus hojas, y destacar las métricas medidas: ×{es(x_id, 0)} en búsqueda por ID, ×{es(x_rango, 0)} en consultas por "
    f"rango y −{es(red_exp * 100, 0)} % de nodos explorados con A*.",
])

# ======================================================================== BIBLIOGRAFÍA (APA 7)
H1("Referencias")
refs = [
    "Bayer, R., y McCreight, E. (1972). Organization and maintenance of large ordered indexes. _Acta Informatica, 1_(3), 173–189. https://doi.org/10.1007/BF00288683",
    "Calatayud, A., Sánchez González, S., Bedoya Maya, F., Giraldez Zúñiga, F., y Márquez, J. M. (2021). _Congestión urbana en América Latina y el Caribe: características, costos y mitigación_. Banco Interamericano de Desarrollo. https://publications.iadb.org/es/congestion-urbana-en-america-latina-y-el-caribe-caracteristicas-costos-y-mitigacion",
    "Colaboradores de OpenStreetMap. (2026). _OpenStreetMap_ [Conjunto de datos; extracto de vías principales de Santa Cruz de la Sierra obtenido con la API Overpass el 16 de noviembre de 2026]. https://www.openstreetmap.org",
    "Comer, D. (1979). The ubiquitous B-tree. _ACM Computing Surveys, 11_(2), 121–137. https://doi.org/10.1145/356770.356776",
    "Cormen, T. H., Leiserson, C. E., Rivest, R. L., y Stein, C. (2009). _Introduction to algorithms_ (3.ª ed.). MIT Press.",
    "Correo del Sur. (4 de junio de 2023). El parque automotor de Bolivia se quintuplicó en casi 20 años. https://correodelsur.com/sociedad/20230604/el-parque-automotor-de-bolivia-se-quintuplico-en-casi-20-anos.html",
    "Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. _Numerische Mathematik, 1_(1), 269–271. https://doi.org/10.1007/BF01386390",
    "El País. (30 de agosto de 2024). Bolivia supera los 11,3 millones de habitantes; Santa Cruz es el departamento más poblado. https://elpais.bo/nacional/20240830_bolivia-supera-los-11-3-millones-de-habitantes.html",
    "eju.tv. (15 de junio de 2026a). En Santa Cruz circulan cerca de un millón de vehículos, el 36,4 % del parque automotor nacional. https://eju.tv/?p=5010852",
    "eju.tv. (2026b). Parque automotor en Bolivia crece en 3,4 % y supera los 2,67 MM de vehículos. https://eju.tv/?p=5009663",
    "Elmasri, R., y Navathe, S. B. (2016). _Fundamentals of database systems_ (7.ª ed.). Pearson.",
    "Google. (s.f.). _Traffic, transit, and bicycling layers_. Google Maps Platform. Recuperado el 1 de noviembre de 2026 de https://developers.google.com/maps/documentation/javascript/trafficlayer",
    "Haklay, M., y Weber, P. (2008). OpenStreetMap: User-generated street maps. _IEEE Pervasive Computing, 7_(4), 12–18. https://doi.org/10.1109/MPRV.2008.80",
    "Hart, P. E., Nilsson, N. J., y Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. _IEEE Transactions on Systems Science and Cybernetics, 4_(2), 100–107. https://doi.org/10.1109/TSSC.1968.300136",
    "Hernández Sampieri, R., y Mendoza Torres, C. P. (2018). _Metodología de la investigación: las rutas cuantitativa, cualitativa y mixta_. McGraw-Hill Interamericana.",
    "Howe, J. (2006). The rise of crowdsourcing. _Wired, 14_(6). https://www.wired.com/2006/06/crowds/",
    "Leaflet. (s.f.). _Leaflet: an open-source JavaScript library for interactive maps_. Recuperado el 1 de noviembre de 2026 de https://leafletjs.com/",
    "Los Tiempos. (9 de abril de 2024). Aumenta en 5,3 % el parque automotor en Bolivia. https://www.lostiempos.com/actualidad/economia/20240409/aumenta-53-parque-automotor-bolivia",
    "Nielsen, J. (1993). _Usability engineering_. Academic Press.",
    "ORCID. (s.f.). _What is ORCID?_ Recuperado el 9 de noviembre de 2026 de https://info.orcid.org/what-is-orcid/",
    "Sedgewick, R., y Wayne, K. (2011). _Algorithms_ (4.ª ed.). Addison-Wesley.",
    "Waze. (s.f.). _Waze for Cities_. Recuperado el 1 de noviembre de 2026 de https://www.waze.com/wazeforcities",
    "Wikimedia Commons. (s.f.). _Fotografías de avenidas de Santa Cruz de la Sierra, Bolivia_ [Fotografías con licencia libre]. Recuperado el 16 de noviembre de 2026 de https://commons.wikimedia.org/",
]
for ref in refs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Cm(1.27)
    p.paragraph_format.first_line_indent = Cm(-1.27)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(0)
    agregar_runs(p, ref, 12)

# ======================================================================== ANEXOS
H1("Anexos")
H2("Anexo A: Matriz de atención a las observaciones de la tutoría")
P(f"La Tabla {n_tab + 1} detalla cómo se atendió cada observación del informe de evaluación del 13 de octubre de 2026, y la "
  f"Tabla {n_tab + 2}, las observaciones de la revisión de noviembre de 2026.")
tabla(["Observación de la tutoría", "Corrección realizada", "Ubicación"],
      [["Carátula: falta número de proyecto y tipografía institucional", "Se corrigió el nombre de la facultad («INGENIERÍA»), se unificó la tipografía (Times New Roman) y se añadió el campo «Proyecto N°» para el número oficial; se acortó el título del proyecto", "Carátula"],
       ["Resumen y Abstract con errores de notación (O(log n) duplicado)", "Se limpió toda la notación matemática y se actualizaron ambos textos con los resultados medidos", "Resumen, Abstract"],
       ["Marcadores sin completar ([TU CIUDAD], [INSERTAR DATO])", "Se reemplazaron por datos reales: Censo 2024, parque automotor INE/RUAT 2022–2025, BID (2021) y la estructura de anillos y radiales de Santa Cruz", "1.1, 2.2, Tabla 1"],
       ["Falta la hipótesis (apartado 2.4)", "Se añadieron una hipótesis general, tres específicas con umbrales medibles y la hipótesis nula", "2.4"],
       ["Falta un marco metodológico con diseño, variables e indicadores", "Nuevo capítulo 5: tipo, enfoque, diseño, variables, muestra, instrumentos, procedimiento, criterios y matriz de consistencia", "Capítulo 5"],
       ["Cada objetivo debe tener un entregable medible", "Matriz de objetivos, entregables, indicadores y resultados", "Tabla 2"],
       ["Fórmulas duplicadas en la propuesta (M = 5M = 5)", "Se corrigieron todas las expresiones", "Capítulos 4 y 6"],
       ["Añadir una ilustración de las hojas enlazadas del Árbol B+", "Nueva figura de un Árbol B+ de orden 5 con el recorrido de una consulta por rango", "Figura 1"],
       ["Aclarar si el Árbol B+ se implementó desde cero", "Se declara explícitamente; el grafo también se implementó desde cero en lugar de NetworkX", "7.3, 7.4, Anexos B y C"],
       ["Convertir las tablas de resultados en gráficos de líneas", "Gráficos de tiempo frente a número de reportes y de nodos; las tablas pasan a ser medidas reales", "8.3, 8.4, 8.6"],
       ["Formalizar la bibliografía (APA 7 o IEEE) con citas en el texto", "Lista de referencias en APA 7 con 23 fuentes citadas en el texto; todo el documento sigue el formato APA 7 (interlineado doble, márgenes de 2,54 cm, número de página arriba a la derecha, niveles de títulos y tablas)", "Referencias"],
       ["Feria: demostración interactiva, visualización didáctica y póster con métricas", f"Página web publicada con «Modo feria», visualizador del Árbol B+ y métricas medidas: {URL_WEB}", "7.6, Recomendaciones"],
       ["Corrección adicional del equipo", "El dato del BID (2 %–4 % del PIB) se corrigió por el valor publicado (0,55 %–1,12 %); los resultados estimados se reemplazaron por mediciones", "1.1, Capítulo 8"]],
      [5.0, 7.6, 2.9], "Atención a las observaciones de la tutoría", tam=9, alinear_num=False)
tabla(["Observación de la revisión", "Corrección realizada", "Ubicación"],
      [["La pregunta menciona fuentes externas que no se implementan", "Se retiró «con fuentes externas de datos viales»; la pregunta se centra en la participación ciudadana", "2.3"],
       ["OE1: un Árbol B+ ordena por una sola clave", "OE1 y la Tabla 2 precisan la doble indexación (por id y por (timestamp, id)); 6.2 explica las dos instancias", "3.2, Tabla 2, 6.2"],
       ["Vínculo débil entre el problema y OE4 (BFS)", "Se añadió en 2.2 el efecto de desborde de la congestión hacia las calles adyacentes", "2.2"],
       ["6.4 describe la nube, pero el prototipo corre en el navegador", "Se aclaró que el prototipo conserva la imagen en el cliente y que Firebase corresponde a producción", "6.4"],
       ["aplicar_reporte() penaliza ambos sentidos", "Nuevo parámetro bidireccional=False: por defecto solo se penaliza el sentido reportado; pruebas de corrección ampliadas; la web permite elegir", "6.3, Anexo C, web"],
       ["Destacar la topología radio-concéntrica en 8.4", "Nueva sección 8.5: medición de A* y Dijkstra sobre la red vial real de Santa Cruz (OpenStreetMap)", "8.5"],
       ["Indicador de OE5 (KB) sin medir", "Se midieron 5 fotografías reales con el código del prototipo: −98,3 % en promedio", "8.7, Tabla 2"],
       ["Conclusiones 1, 4, 5 y 7 sin datos numéricos o incompletas", "Se añadieron el costo de inserción, los 6,1 µs de BFS, la reducción en KB y el cumplimiento del objetivo general", "Conclusiones"],
       ["Errores de sintaxis en el código y símbolos µs y × perdidos", "Se verificó el PDF original: el código y los símbolos están completos (la pérdida ocurre al convertirlo a texto). Se cambió la fuente del código a Courier New y el «÷» por «/»", "7.3, 7.4, Anexos B y C"],
       ["Completar los ORCID pendientes", "Se completaron los identificadores ORCID de los cinco integrantes", "Página 2"]],
      [5.0, 7.6, 2.9], "Atención a la revisión de noviembre de 2026", tam=9, alinear_num=False)
H2("Anexo B: Código fuente del Árbol B+")
P("Archivo arbol_bplus.py (implementación propia, sin bibliotecas externas):", sangria=False)
codigo(open(os.path.join(BASE, "arbol_bplus.py"), encoding="utf-8").read(), 7.5)
H2("Anexo C: Código fuente del Grafo Pesado")
P("Archivo grafo_trafico.py (implementación propia; heapq y deque son de la biblioteca estándar de Python):", sangria=False)
codigo(open(os.path.join(BASE, "grafo_trafico.py"), encoding="utf-8").read(), 7.5)
H2("Anexo D: Reproducción de los experimentos")
P(f"Los scripts se encuentran en la carpeta investigacion/codigo del repositorio {REPO}. Para reproducir los resultados:", sangria=False)
codigo('''python pruebas_correccion.py          # verifica el Árbol B+ y A* contra referencias
python benchmark.py resultados.json   # mide tiempos (semilla fija = 2026)
python figuras.py resultados.json ../figuras
python red_osm.py santa_cruz_vias.json resultados_osm.json red_santa_cruz.json   # red real (OSM)
# compresión: abrir medir_compresion.html en el navegador junto a las fotos''')
H2("Anexo E: Manual de usuario del prototipo web")
numerada([
    f"Ingrese a {URL_WEB} desde una computadora o un teléfono.",
    "En la sección «Demo interactiva», con la pestaña «1 · Calcular ruta», haga clic en el mapa para elegir el origen (A) y luego el destino (B).",
    "Para reportar un incidente, abra la pestaña «2 · Reportar incidente», elija el tipo, marque «Afecta ambos sentidos» si corresponde, adjunte una foto si lo desea y haga clic sobre una calle.",
    "Observe el registro de actividad: muestra la inserción en el Árbol B+, el nuevo peso de la calle y el tiempo de recálculo de la ruta.",
    "Vote los reportes activos con ▲ (confirmar) o ▼ (desmentir); con 3 votos o más se aplican las reglas de confianza.",
    "Use «Modo feria» para bloquear un tramo de la ruta actual y ver el desvío inmediato. «Limpiar reportes» restablece los pesos.",
    "En «Consulta por rango», elija una franja horaria y presione «Buscar reportes» para consultar el historial en el Árbol B+.",
    "En «¿Cómo funciona el Árbol B+?», inserte claves y ejecute consultas por rango para ver el recorrido por las hojas enlazadas.",
])
H2("Anexo F: Capturas de pantalla adicionales")
figura("cap_resultados.png", "Sección de resultados del prototipo web", 15, f"Captura de {URL_WEB}.")
figura("cap_equipo.png", "Sección del equipo con carreras e identificadores ORCID", 15, f"Captura de {URL_WEB}.")

# ======================================================================== índice estático
def llenar_indice():
    usados = 0
    for nivel, texto in TITULOS_INDICE:
        if usados >= len(INDICE_PARRAFOS):
            break
        p = INDICE_PARRAFOS[usados]; usados += 1
        p.paragraph_format.left_indent = Cm({1: 0, 2: 0.6, 3: 1.2}[nivel])
        pPr = p._p.get_or_add_pPr()
        tabs = OxmlElement("w:tabs"); tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right"); tab.set(qn("w:leader"), "dot"); tab.set(qn("w:pos"), "9070")
        tabs.append(tab); pPr.append(tabs)
        r = p.add_run(texto); r.font.size = Pt(11 if nivel > 1 else 11.5); r.bold = nivel == 1
        r2 = p.add_run("\t" + str(PAGINAS.get(texto, ""))); r2.font.size = Pt(11)
    for p in INDICE_PARRAFOS[usados:]:
        p._p.getparent().remove(p._p)
    return len(TITULOS_INDICE)


n_titulos = llenar_indice()
doc.core_properties.title = "TrafficLive: Árboles B+ y Grafos Pesados para reportar y evitar atascos en Santa Cruz de la Sierra"
doc.core_properties.author = "Estaca Paco S., Cruz Rojas A. A., Perez Sandoval W. N., Murguia Duran P. A., Roca Camacho A. F."
doc.save(sys.argv[1])
json.dump([t for _, t in TITULOS_INDICE], open(os.path.splitext(sys.argv[1])[0] + "_titulos.json", "w", encoding="utf-8"), ensure_ascii=False)
print("ok", n_titulos, "títulos,", n_tab, "tablas,", n_fig, "figuras")
