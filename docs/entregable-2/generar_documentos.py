"""Genera los documentos Word del Entregable 2."""

from __future__ import annotations

from pathlib import Path
import subprocess

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "entregables"
ASSETS = OUT / "assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

TEAM = [
    "Luis Gabriel López Vega",
    "Alexis Chavez Mendoza",
    "Daniel Orlando Ceja Olloqui",
    "David Melgoza Martinez",
]


def create_diagrams() -> None:
    diagrams = {
        "mapa_conceptual": r'''
digraph G {
  graph [rankdir=TB, bgcolor="white", pad=0.25, nodesep=0.35, ranksep=0.55];
  node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, color="#94A3B8", fillcolor="#F8FAFC", margin="0.13,0.08"];
  edge [color="#64748B", arrowsize=0.7, fontname="Arial", fontsize=8];
  agente [label="Agente inteligente\nde riego", fillcolor="#DCFCE7", color="#16A34A"];
  parcela [label="Parcela"];
  conocimiento [label="Conocimiento"];
  razonamiento [label="Razonamiento"];
  cultivo [label="Cultivo"];
  suelo [label="Suelo o sustrato"];
  mediciones [label="Mediciones"];
  rag [label="Documentos RAG"];
  reglas [label="Reglas"];
  bayes [label="Bayes"];
  recomendacion [label="Recomendación\nexplicable", fillcolor="#DBEAFE", color="#2563EB"];
  agente -> parcela [label="analiza"];
  agente -> conocimiento [label="consulta"];
  agente -> razonamiento [label="ejecuta"];
  parcela -> cultivo [label="contiene"];
  parcela -> suelo [label="usa"];
  parcela -> mediciones [label="presenta"];
  conocimiento -> rag;
  razonamiento -> reglas;
  razonamiento -> bayes;
  rag -> recomendacion;
  reglas -> recomendacion;
  bayes -> recomendacion;
}
''',
        "arquitectura": r'''
digraph G {
  graph [rankdir=LR, bgcolor="white", pad=0.3, nodesep=0.45, ranksep=0.65];
  node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, color="#94A3B8", fillcolor="#F8FAFC", margin="0.14,0.09"];
  edge [color="#64748B", arrowsize=0.75, fontname="Arial", fontsize=8];
  usuario [label="Usuario\nNavegador", fillcolor="#DBEAFE", color="#2563EB"];
  fastapi [label="FastAPI\nPOST /chat", fillcolor="#DCFCE7", color="#16A34A"];
  langchain [label="LangChain\ny Groq"];
  chroma [label="Chroma\nBase vectorial"];
  reglas [label="Motor de\nreglas"];
  bayes [label="Módulo\nBayes"];
  django [label="Django y DRF\nAPI de gestión", fillcolor="#FEF3C7", color="#D97706"];
  sqlite [label="SQLite\nPersistencia"];
  docs [label="Documentos\nknowledge"];
  usuario -> fastapi [label="HTTP JSON"];
  fastapi -> langchain [label="prompt + contexto"];
  fastapi -> chroma [label="recuperación"];
  fastapi -> reglas [label="hechos"];
  fastapi -> bayes [label="evidencias"];
  docs -> chroma [label="ingesta"];
  fastapi -> django [label="registro tolerante\na fallos"];
  django -> sqlite;
}
''',
    }
    for name, dot in diagrams.items():
        dot_path = ASSETS / f"{name}.dot"
        png_path = ASSETS / f"{name}.png"
        dot_path.write_text(dot, encoding="utf-8")
        subprocess.run(["dot", "-Tpng", "-Gdpi=180", str(dot_path), "-o", str(png_path)], check=True)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=110, start=120, bottom=110, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def style_table(table, widths=None) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    header = table.rows[0]
    set_repeat_table_header(header)
    for idx, cell in enumerate(header.cells):
        set_cell_shading(cell, "1F4E78")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.left_indent = Inches(0)
            paragraph.paragraph_format.right_indent = Inches(0)
            paragraph.paragraph_format.first_line_indent = Inches(0)
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(9)
    for row_idx, row in enumerate(table.rows[1:], start=1):
        for col_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if row_idx % 2 == 0:
                set_cell_shading(cell, "EEF4F8")
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.left_indent = Inches(0)
                paragraph.paragraph_format.right_indent = Inches(0)
                paragraph.paragraph_format.first_line_indent = Inches(0)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    if widths:
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Inches(width)


def setup_document(title: str) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.82)
    section.right_margin = Inches(0.82)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    for name, size in (("Title", 26), ("Heading 1", 16), ("Heading 2", 12.5), ("Heading 3", 11)):
        style = styles[name]
        style.font.name = "Aptos Display" if name != "Normal" else "Aptos"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(11 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True
    styles["Title"].paragraph_format.space_after = Pt(16)

    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Agente Inteligente de Riego   Entregable 2")
    run.font.name = "Aptos"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(100, 116, 139)
    doc.core_properties.title = title
    doc.core_properties.subject = "Proyecto de IA Agéntica"
    return doc


def add_cover(doc: Document, title: str, subtitle: str) -> None:
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(title)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(subtitle)
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Proyecto de IA Agéntica")
    r.font.size = Pt(12)
    r.font.bold = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Equipo").bold = True
    for member in TEAM:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.add_run(member)
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Fecha oficial de entrega 9 de octubre de 2026").italic = True
    doc.add_page_break()


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.23)
        p.paragraph_format.first_line_indent = Inches(-0.23)
        p.paragraph_format.space_after = Pt(3)
        p.add_run(f"•  {item}")


def add_numbered(doc: Document, items: list[str], start: int = 1) -> None:
    for number, item in enumerate(items, start=start):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.23)
        p.paragraph_format.first_line_indent = Inches(-0.23)
        p.paragraph_format.space_after = Pt(3)
        p.add_run(f"{number}.  {item}")


def add_code(doc: Document, code: str) -> None:
    for line in code.strip().splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line)
        r.font.name = "Cascadia Mono"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(30, 41, 59)


def build_technical_document() -> Path:
    doc = setup_document("Documentación del Entregable 2 del agente inteligente de riego")
    add_cover(
        doc,
        "Documentación del Entregable 2",
        "Representación del conocimiento y razonamiento del agente",
    )

    doc.add_heading("Resumen ejecutivo", level=1)
    doc.add_paragraph(
        "AgroRiego IA evolucionó de un chatbot mínimo a un agente capaz de recuperar conocimiento propio, ejecutar reglas deterministas, estimar incertidumbre y conservar evidencia administrativa. La solución mantiene FastAPI como servicio de inferencia, incorpora Chroma para RAG y agrega un microservicio Django con Django REST Framework."
    )
    doc.add_paragraph(
        "El resultado cumple el alcance funcional del Entregable 2: RAG operativo, motor de reglas integrado, módulo probabilístico simple, API de gestión y planeación de dos sprints adicionales. Los umbrales y probabilidades son académicos y están identificados como valores que requieren calibración antes de cualquier uso real."
    )

    doc.add_heading("Alcance y cumplimiento", level=1)
    rows = [
        ("Mapa conceptual y red semántica", "Cumplido", "Modelo de entidades, relaciones y jerarquías"),
        ("Base documental", "Cumplido", "Siete documentos temáticos en knowledge"),
        ("Base vectorial", "Cumplido", "Chroma persistente local"),
        ("Pipeline RAG", "Cumplido", "Carga, chunking, embeddings, almacenamiento y retriever"),
        ("Sistema basado en reglas", "Cumplido", "Hechos, reglas codificadas y explicación"),
        ("Teorema de Bayes", "Cumplido", "Actualización de odds mediante evidencias"),
        ("Django y DRF", "Cumplido", "Modelos, administración y API REST"),
        ("Integración de servicios", "Cumplido", "Contrato HTTP JSON tolerante a fallos"),
        ("Sprint 3 y Sprint 4", "Preparado", "Backlog, responsables, puntos y evidencias"),
    ]
    table = doc.add_table(rows=1, cols=3)
    table.rows[0].cells[0].text = "Requisito"
    table.rows[0].cells[1].text = "Estado"
    table.rows[0].cells[2].text = "Evidencia"
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [2.45, 1.0, 3.35])

    doc.add_heading("Modelado del conocimiento", level=1)
    doc.add_paragraph(
        "El dominio se organiza alrededor de la parcela, el cultivo, el suelo o sustrato, las mediciones aportadas por el usuario y los mecanismos de razonamiento. El agente transforma la consulta en hechos, recupera fragmentos relacionados y combina ambas entradas antes de solicitar una respuesta al modelo."
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(ASSETS / "mapa_conceptual.png"), width=Inches(6.25))
    p = doc.add_paragraph("Figura 1 Mapa conceptual del dominio")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9)

    doc.add_heading("Red semántica", level=2)
    relations = [
        ("Parcela", "contiene", "Cultivo"),
        ("Cultivo", "crece en", "Suelo o sustrato"),
        ("Sensor", "produce", "Medición"),
        ("Regla", "evalúa", "Hechos"),
        ("Módulo Bayes", "combina", "Evidencias"),
        ("Documento", "fundamenta", "Recomendación"),
        ("Agente", "registra", "Conversación y auditoría"),
    ]
    table = doc.add_table(rows=1, cols=3)
    for cell, value in zip(table.rows[0].cells, ("Entidad origen", "Relación", "Entidad destino")):
        cell.text = value
    for row in relations:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [2.0, 2.0, 2.8])

    doc.add_heading("Base documental", level=2)
    add_bullets(doc, [
        "Principios de riego responsable.",
        "Suelos y sustratos.",
        "Cultivos principales: tomate y fresa.",
        "Sensores y calidad de los datos.",
        "Seguridad del sistema de riego.",
        "Preguntas frecuentes.",
        "Política de respuesta del agente.",
    ])

    doc.add_heading("Implementación de RAG", level=1)
    doc.add_paragraph(
        "La ingesta recorre archivos Markdown y texto, normaliza su contenido y lo divide en fragmentos con solapamiento. Cada fragmento recibe un identificador estable, metadatos de fuente y un vector de 384 dimensiones. Chroma conserva documentos, metadatos y embeddings en una colección persistente."
    )
    add_numbered(doc, [
        "Carga de archivos desde la carpeta knowledge.",
        "División en fragmentos de aproximadamente 900 caracteres con solapamiento.",
        "Generación local de embeddings reproducibles mediante hashing de palabras y bigramas.",
        "Almacenamiento de vectores y metadatos en Chroma.",
        "Búsqueda por similitud y recuperación de los cuatro fragmentos más cercanos.",
        "Inyección del contexto, las fuentes y las limitaciones en el prompt de LangChain.",
    ])
    doc.add_paragraph(
        "La estrategia de embeddings evita descargar otro modelo durante la instalación y facilita la demostración. Su limitación es una comprensión semántica menor que la de un modelo entrenado; por ello se documenta como una decisión académica reproducible."
    )

    doc.add_heading("Sistema basado en reglas", level=1)
    doc.add_paragraph(
        "El motor aplica encadenamiento hacia adelante: primero extrae hechos de la consulta y después evalúa condiciones. Cada conclusión conserva el código de la regla que la produjo."
    )
    rules = [
        ("R-HUM-01", "Humedad menor a 25 %", "Revisar cultivo y considerar riego"),
        ("R-HUM-02", "Humedad entre 25 % y 70 %", "Confirmar umbral del cultivo"),
        ("R-HUM-03", "Humedad mayor a 70 %", "Posponer y revisar drenaje"),
        ("R-TEMP-01", "Temperatura igual o mayor a 32 °C", "Priorizar inspección y evitar horas críticas"),
        ("R-CLIMA-01", "Lluvia esperada", "Posponer hasta verificar pronóstico y humedad"),
        ("R-CLIMA-02", "Humedad baja y sin lluvia", "Aumentar prioridad de revisión"),
        ("R-SUELO-01", "Suelo arenoso y humedad menor a 35 %", "Aplicaciones controladas y revisión frecuente"),
        ("R-SEG-01", "Solicitud de accionar equipo", "Bloquear acción y requerir verificación humana"),
    ]
    table = doc.add_table(rows=1, cols=3)
    for cell, value in zip(table.rows[0].cells, ("Código", "Condición", "Conclusión")):
        cell.text = value
    for row in rules:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [1.0, 2.65, 3.15])

    doc.add_heading("Razonamiento probabilístico", level=1)
    doc.add_paragraph(
        "El módulo parte de una probabilidad previa demostrativa de 35 % de necesidad de riego. Cada evidencia modifica los odds mediante una razón de verosimilitud. La relación aplicada es: odds posteriores = odds previos × producto de razones de verosimilitud. Finalmente, los odds se convierten nuevamente en probabilidad."
    )
    evidence = [
        ("Humedad baja", "5.00", "Incrementa fuertemente"),
        ("Humedad alta", "0.12", "Reduce fuertemente"),
        ("Temperatura alta", "1.80", "Incrementa"),
        ("Lluvia esperada", "0.25", "Reduce"),
        ("Sin lluvia esperada", "1.50", "Incrementa"),
        ("Suelo arenoso", "1.40", "Incrementa"),
    ]
    table = doc.add_table(rows=1, cols=3)
    for cell, value in zip(table.rows[0].cells, ("Evidencia", "Razón", "Efecto")):
        cell.text = value
    for row in evidence:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [2.55, 1.0, 3.25])
    doc.add_paragraph(
        "Ejemplo: humedad de 18 %, temperatura de 34 °C, suelo arenoso y ausencia de lluvia producen una probabilidad alta. El agente muestra las evidencias y advierte que el resultado no ha sido calibrado con datos de campo."
    )

    doc.add_heading("Arquitectura de microservicios", level=1)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(ASSETS / "arquitectura.png"), width=Inches(6.7))
    p = doc.add_paragraph("Figura 2 Arquitectura funcional del Entregable 2")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9)

    doc.add_heading("Microservicio FastAPI", level=2)
    add_bullets(doc, [
        "Valida las solicitudes con Pydantic.",
        "Mantiene una ventana de memoria por session id.",
        "Consulta Chroma y ejecuta reglas y Bayes.",
        "Invoca el modelo mediante LangChain y Groq.",
        "Devuelve fuentes, reglas, probabilidad y estado del registro administrativo.",
    ])
    doc.add_heading("Microservicio Django y DRF", level=2)
    models = [
        ("Conversation", "Sesión y usuario opcional"),
        ("Message", "Mensajes del usuario y del agente con metadatos"),
        ("AuditLog", "Eventos y trazabilidad"),
        ("RuleConfig", "Configuración administrativa de reglas"),
        ("KnowledgeDocument", "Registro de documentos indexables"),
    ]
    add_bullets(doc, [f"{model}: {responsibility}" for model, responsibility in models])

    doc.add_heading("Contrato de comunicación", level=2)
    doc.add_paragraph(
        "FastAPI envía cada interacción a POST /api/exchanges/. Django crea o recupera la conversación, almacena el mensaje del usuario, la respuesta y un registro de auditoría. Si el servicio de gestión no está disponible, FastAPI responde normalmente y establece management_logged en false."
    )

    doc.add_heading("Pruebas y validación", level=1)
    tests = [
        ("API FastAPI", "6", "Salud, interfaz, validación, chat, memoria y cliente Groq"),
        ("Reglas y Bayes", "3", "Humedad baja, humedad alta y seguridad"),
        ("RAG", "3", "Embeddings, chunking e integración Chroma"),
        ("Django DRF", "1", "Persistencia completa de un intercambio"),
        ("Prueba de humo", "1", "Arranque simultáneo y comunicación HTTP"),
    ]
    table = doc.add_table(rows=1, cols=3)
    for cell, value in zip(table.rows[0].cells, ("Grupo", "Cantidad", "Resultado")):
        cell.text = value
    for row in tests:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [1.6, 1.0, 4.2])
    doc.add_paragraph(
        "Resultado verificado: 12 pruebas de pytest aprobadas, 1 prueba de Django aprobada, migraciones aplicadas, 9 fragmentos indexados y comprobación HTTP satisfactoria entre los servicios."
    )

    doc.add_page_break()
    doc.add_heading("Gestión Scrum", level=1)
    sprints = [
        ("Sprint 3", "Conocimiento y RAG", "21 sep al 2 oct", "6", "29"),
        ("Sprint 4", "Reglas Bayes y gestión", "5 al 9 oct", "6", "28"),
    ]
    table = doc.add_table(rows=1, cols=5)
    for cell, value in zip(table.rows[0].cells, ("Sprint", "Objetivo", "Fechas", "Tareas", "Puntos")):
        cell.text = value
    for row in sprints:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [1.1, 2.45, 1.35, 0.8, 0.8])
    doc.add_paragraph(
        "El backlog incluye doce tareas con responsables equilibrados, criterios de aceptación, fechas y puntos. También se prepararon planning, daily, review y retrospectiva. El Sprint 4 se comprimió para respetar la fecha oficial del 9 de octubre."
    )

    doc.add_heading("Instalación y demostración", level=1)
    add_numbered(doc, [
        "Ejecutar .\\instalar.bat desde PowerShell.",
        "Colocar una clave personal de Groq en el archivo .env.",
        "Confirmar un modelo disponible en GROQ_MODEL.",
        "Ejecutar .\\iniciar_todo.bat.",
        "Abrir http://127.0.0.1:8000 y realizar una consulta con datos de humedad, temperatura, suelo y lluvia.",
        "Comprobar conversaciones y auditoría en http://127.0.0.1:8001/api/.",
    ])

    doc.add_heading("Limitaciones y trabajo futuro", level=1)
    add_bullets(doc, [
        "Los embeddings por hashing no igualan la comprensión semántica de un modelo especializado.",
        "Los umbrales y probabilidades necesitan calibración con datos locales.",
        "SQLite y los permisos abiertos son adecuados para demostración, no para producción.",
        "No existe conexión con sensores, clima en tiempo real o actuadores.",
        "Una versión futura debe agregar autenticación, despliegue y observabilidad.",
    ])

    doc.add_heading("Conclusión", level=1)
    doc.add_paragraph(
        "El agente cumple el objetivo del Entregable 2 al combinar memoria semántica, conocimiento recuperable, lógica determinista, incertidumbre y persistencia administrativa. La solución es reproducible, ejecutable localmente y mantiene límites claros para evitar presentar una demostración académica como un sistema autónomo de riego real."
    )

    path = OUT / "Documentacion_Entregable2_AgroRiego_IA.docx"
    doc.save(path)
    return path


def build_installation_guide() -> Path:
    doc = setup_document("Guía de instalación del Entregable 2 de AgroRiego IA")
    add_cover(
        doc,
        "Guía de instalación y demostración",
        "AgroRiego IA Entregable 2",
    )
    doc.add_heading("Propósito", level=1)
    doc.add_paragraph(
        "Esta guía permite instalar, iniciar y comprobar el agente completo en Windows. La instalación prepara FastAPI, Chroma, Django, DRF y las pruebas sin requerir configuración manual de bases de datos. Cada integrante debe utilizar su propia clave de Groq."
    )

    doc.add_heading("Requisitos", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Elemento"
    table.rows[0].cells[1].text = "Requisito"
    for row in [
        ("Sistema", "Windows 10 u 11"),
        ("Python", "3.11 o 3.12 con Add Python to PATH"),
        ("Internet", "Necesario para instalar y consultar Groq"),
        ("Clave", "Una GROQ_API_KEY personal"),
        ("Puertos", "8000 para FastAPI y 8001 para Django"),
    ]:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [2.0, 4.8])

    doc.add_heading("Instalación inicial", level=1)
    add_numbered(doc, [
        "Extraer completamente el archivo ZIP. No ejecutar el proyecto dentro del archivo comprimido.",
        "Entrar en la carpeta agente-riego-ia.",
        "Hacer clic derecho en un espacio vacío y seleccionar Abrir en Terminal.",
        "Comprobar Python con python --version.",
        "Ejecutar .\\instalar.bat.",
        "Esperar a que se instalen las dependencias, se apliquen migraciones y se indexen los documentos.",
    ])
    doc.add_heading("Comando correcto en PowerShell", level=2)
    add_code(doc, r".\instalar.bat")
    doc.add_paragraph(
        "PowerShell no busca automáticamente ejecutables en la carpeta actual. Si se escribe solo instalar.bat puede aparecer el mensaje de comando no reconocido; el prefijo .\\ evita ese problema."
    )

    doc.add_heading("Configuración de Groq", level=1)
    add_numbered(doc, [
        "Abrir el archivo .env con Bloc de notas o Visual Studio Code.",
        "Reemplazar únicamente el valor de GROQ_API_KEY.",
        "Comprobar que GROQ_MODEL corresponda a un modelo disponible en la cuenta.",
        "Guardar el archivo y reiniciar el agente si ya estaba abierto.",
    ], start=7)
    add_code(doc, "GROQ_API_KEY=gsk_coloca_aqui_tu_clave\nGROQ_MODEL=openai/gpt-oss-20b\nRAG_TOP_K=4\nDJANGO_LOGGING_ENABLED=true")
    doc.add_paragraph(
        "No se debe enviar el archivo .env por mensajes ni agregarlo a Git. El proyecto incluye .env.example sin secretos."
    )

    doc.add_heading("Inicio de los servicios", level=1)
    add_code(doc, r".\iniciar_todo.bat")
    doc.add_paragraph(
        "El comando abre Django en una segunda terminal y mantiene FastAPI en la terminal principal. Ambas ventanas deben permanecer abiertas durante la demostración."
    )
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Dirección"
    table.rows[0].cells[1].text = "Uso"
    for row in [
        ("http://127.0.0.1:8000", "Chatbot"),
        ("http://127.0.0.1:8000/health", "Estado de Groq, RAG y Django"),
        ("http://127.0.0.1:8000/docs", "Swagger de FastAPI"),
        ("http://127.0.0.1:8001/api/", "API de gestión"),
        ("http://127.0.0.1:8001/admin/", "Panel administrativo"),
    ]:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [3.4, 3.4])

    doc.add_heading("Comprobación de la base vectorial", level=1)
    doc.add_paragraph(
        "El endpoint /health debe indicar rag_ready true y una cantidad de fragmentos mayor que cero. Para reconstruir el índice después de editar los documentos, ejecutar:"
    )
    add_code(doc, r".\ingerir_conocimiento.bat")

    doc.add_heading("Prueba funcional sugerida", level=1)
    doc.add_paragraph(
        "Enviar esta pregunta desde la interfaz web:"
    )
    add_code(doc, "Tengo jitomate en suelo arenoso, humedad 18 %, temperatura 34 y no se espera lluvia. ¿Debo regar?")
    doc.add_paragraph("La respuesta debe mostrar:")
    add_bullets(doc, [
        "Orientación basada en los datos proporcionados.",
        "Al menos una fuente documental.",
        "Reglas como R-HUM-01, R-TEMP-01 o R-SUELO-01.",
        "Una probabilidad bayesiana identificada como demostrativa.",
        "Una advertencia de verificación humana.",
    ])

    doc.add_heading("Pruebas automatizadas", level=1)
    add_code(doc, r".\.venv\Scripts\python.exe -m pytest -q")
    add_code(doc, r".\.venv\Scripts\python.exe management_service\manage.py test core")
    doc.add_paragraph(
        "Resultado verificado en el paquete entregado: 12 pruebas del agente y 1 prueba de Django aprobadas."
    )

    doc.add_page_break()
    doc.add_heading("Crear acceso al panel Django", level=1)
    add_code(doc, r".\.venv\Scripts\python.exe management_service\manage.py createsuperuser")
    doc.add_paragraph(
        "Este paso es opcional para la demostración. Django solicitará nombre de usuario, correo y contraseña local."
    )

    doc.add_heading("Solución de problemas", level=1)
    issues = [
        ("instalar.bat no se reconoce", "Ejecutar .\\instalar.bat desde la carpeta correcta."),
        ("401 de Groq", "Revisar que la clave sea válida y esté completa."),
        ("404 model_not_found", "Cambiar GROQ_MODEL por uno disponible y reiniciar."),
        ("rag_ready false", "Ejecutar ingerir_conocimiento.bat y revisar la carpeta knowledge."),
        ("management_logged false", "Confirmar que la terminal Django siga abierta en el puerto 8001."),
        ("Puerto ocupado", "Cerrar la instancia anterior con Ctrl+C antes de iniciar otra."),
        ("Django sin tablas", "Ejecutar python management_service\\manage.py migrate."),
    ]
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Síntoma"
    table.rows[0].cells[1].text = "Solución"
    for row in issues:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = value
    style_table(table, [2.7, 4.1])

    doc.add_heading("Cierre correcto", level=1)
    doc.add_paragraph(
        "Presionar Ctrl+C en las dos terminales. Los documentos de conocimiento y la base SQLite permanecen guardados; no es necesario repetir instalar.bat para volver a usar el proyecto."
    )
    path = OUT / "Guia_Instalacion_Entregable2_AgroRiego_IA.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    create_diagrams()
    for result in (build_technical_document(), build_installation_guide()):
        print(result)
