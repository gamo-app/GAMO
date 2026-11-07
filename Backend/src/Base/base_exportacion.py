from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
import re
import unicodedata
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from model import UsuarioFiltradoResponse


# El servidor corre en UTC: sin esto, entre las 21:00 y las 24:00 (hora argentina) la fecha
# de los archivos ya sería la del día siguiente. Argentina no tiene horario de verano: UTC-3 fijo.
ZONA_AR = timezone(timedelta(hours=-3))

COLUMNAS_EXPORTACION = [
    ("DNI", "DNI"),
    ("Apellido", "apellido"),
    ("Nombre", "nombre"),
    ("Sede", "sede"),
    ("Clase", "clase"),
    ("Plan", "plan"),
    ("Inicio Membresía", "fecha_inicio_membresia"),
    ("Vencimiento Cuota", "fecha_vencimiento_cuota"),
    ("Estado Cuota", "estado_cuota"),
    ("Monto Cuota", "monto_cuota"),
    ("Estado Usuario", "estado"),
]

CAMPOS_TEXTO_IZQUIERDA = ("nombre", "apellido", "sede", "plan", "clase")

# En el Excel las fechas y los montos van como fecha/número de verdad (se pueden ordenar,
# filtrar y sumar). Este formato solo cambia cómo se ven en la celda.
FORMATOS_XLSX = {
    "fecha_inicio_membresia": "DD/MM/YYYY",
    "fecha_vencimiento_cuota": "DD/MM/YYYY",
    "monto_cuota": '"$"#,##0.00',
}

# Caracteres de control que openpyxl no acepta en una celda: con uno solo en un nombre,
# fallaría la exportación completa.
_CONTROL_XLSX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Letras que Helvetica no tiene y que no se descomponen en "letra + acento".
_EQUIVALENTES_PDF = str.maketrans({"Ł": "L", "ł": "l", "Đ": "D", "đ": "d"})


def ahora_ar() -> datetime:
    return datetime.now(ZONA_AR)


def _formatear_monto(valor) -> str:
    """18000.5 -> '$18.000,50' (formato argentino). Los negativos salen como '-$500,00'."""
    try:
        monto = Decimal(str(valor))
        texto = f"{abs(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"-${texto}" if monto < 0 else f"${texto}"
    except (ArithmeticError, ValueError):
        return f"${valor}"


def _formatear_valor(usuario: UsuarioFiltradoResponse, campo: str) -> str:
    """Texto tal como se ve en pantalla/PDF (el Excel usa _valor_xlsx para guardar el dato real)."""
    valor = getattr(usuario, campo, None)
    if valor is None or valor == "" or (campo == "DNI" and valor == 0):
        return "-"
    if campo in ("fecha_inicio_membresia", "fecha_vencimiento_cuota") and hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    if campo == "monto_cuota":
        return _formatear_monto(valor)
    if campo in ("estado_cuota", "estado"):
        return str(valor).capitalize()
    return str(valor)


def _valor_xlsx(usuario: UsuarioFiltradoResponse, campo: str):
    """Valor que se guarda en la celda: fecha y número reales; el texto, sin caracteres inválidos."""
    valor = getattr(usuario, campo, None)
    if valor is None or valor == "" or (campo == "DNI" and valor == 0):
        return "-"
    if campo in ("estado_cuota", "estado"):
        valor = str(valor).capitalize()
    if isinstance(valor, str):
        return _CONTROL_XLSX.sub("", valor) or "-"
    return valor


def _texto_pdf(texto: str) -> str:
    """Deja solo lo que Helvetica sabe dibujar (cp1252); lo demás saldría como un cuadrado negro."""
    resultado = []
    for c in unicodedata.normalize("NFC", str(texto)).translate(_EQUIVALENTES_PDF):
        if c in "\n\r\t":
            resultado.append(" ")
        elif unicodedata.category(c).startswith("C") or unicodedata.combining(c):
            continue
        else:
            try:
                c.encode("cp1252")
            except UnicodeEncodeError:
                c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode() or "?"
            resultado.append(c)
    return "".join(resultado)


def _subtitulo(total: int) -> str:
    return (
        f"Fecha de exportación: {ahora_ar().strftime('%d/%m/%Y %H:%M')} | "
        f"Total de registros: {total}"
    )


def _texto_filtros(filtros: dict[str, str] | None) -> str | None:
    if not filtros:
        return None
    return "Filtros: " + " | ".join(f"{nombre}: {valor}" for nombre, valor in filtros.items())


def _slug(texto: str | None) -> str:
    sin_acentos = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_acentos.lower()).strip("_")[:40].strip("_")


def nombre_archivo_exportacion(clase: str | None, estado: str | None, ext: str) -> str:
    """Ej.: socios_natacion_lunes_18_00_a_19_00_morosos_gamo_2026-11-06.xlsx (fecha de Argentina).

    Solo deja letras, números y guiones bajos: así el nombre siempre entra en el header
    Content-Disposition (con tildes u otros caracteres raros, la respuesta fallaba con un 500).
    """
    estado_slug = _slug(estado)
    if estado_slug in ("todos", "todas"):
        estado_slug = ""
    partes = ["socios", _slug(clase), estado_slug, "gamo", ahora_ar().date().isoformat()]
    return "_".join(p for p in partes if p) + f".{ext}"


def generar_xlsx_socios(
    usuarios: list[UsuarioFiltradoResponse],
    filtros: dict[str, str] | None = None,
) -> io.BytesIO:
    """Genera un archivo XLSX en memoria con todos los socios filtrados."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Socios"

    total_cols = len(COLUMNAS_EXPORTACION)
    ultima_letra = get_column_letter(total_cols)

    ws.merge_cells(f"A1:{ultima_letra}1")
    celda_titulo = ws["A1"]
    celda_titulo.value = "GAMO - Listado de Socios Exportados"
    celda_titulo.font = Font(name="Calibri", size=14, bold=True, color="1F497D")
    celda_titulo.alignment = Alignment(vertical="center")

    ws.merge_cells(f"A2:{ultima_letra}2")
    ws["A2"] = _subtitulo(len(usuarios))
    ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="595959")
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 18

    texto_filtros = _texto_filtros(filtros)
    if texto_filtros:
        ws.merge_cells(f"A3:{ultima_letra}3")
        ws["A3"] = _CONTROL_XLSX.sub("", texto_filtros)
        ws["A3"].font = Font(name="Calibri", size=9, bold=True, color="1F497D")
        ws.row_dimensions[3].height = 18

    fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_par = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
    borde = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    fila_encabezado = 4
    primera_fila_datos = fila_encabezado + 1
    ws.row_dimensions[fila_encabezado].height = 22
    for col_idx, (titulo_col, _) in enumerate(COLUMNAS_EXPORTACION, start=1):
        celda = ws.cell(row=fila_encabezado, column=col_idx, value=titulo_col)
        celda.fill = fill_header
        celda.font = font_header
        celda.alignment = Alignment(horizontal="center", vertical="center")
        celda.border = borde

    # Ancho de cada columna: el texto más largo (título o dato tal como se ve), entre 12 y 35.
    anchos = [len(titulo_col) for titulo_col, _ in COLUMNAS_EXPORTACION]

    if not usuarios:
        ws.merge_cells(f"A{primera_fila_datos}:{ultima_letra}{primera_fila_datos}")
        celda_vacia = ws[f"A{primera_fila_datos}"]
        celda_vacia.value = "No se encontraron socios para los filtros seleccionados."
        celda_vacia.font = Font(name="Calibri", size=10, italic=True, color="595959")
        celda_vacia.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[primera_fila_datos].height = 22
    else:
        for row_idx, usuario in enumerate(usuarios, start=primera_fila_datos):
            ws.row_dimensions[row_idx].height = 19
            es_par = row_idx % 2 == 0

            for col_idx, (_, campo) in enumerate(COLUMNAS_EXPORTACION, start=1):
                valor = _valor_xlsx(usuario, campo)
                celda = ws.cell(row=row_idx, column=col_idx, value=valor)
                if isinstance(valor, str):
                    # Todo texto se guarda como texto: openpyxl convertiría en fórmula
                    # cualquier valor que empiece con "=" (ej. un nombre cargado a propósito).
                    celda.data_type = "s"
                if campo in FORMATOS_XLSX and valor != "-":
                    celda.number_format = FORMATOS_XLSX[campo]
                celda.font = Font(name="Calibri", size=10)
                celda.border = borde
                if es_par:
                    celda.fill = fill_par

                if campo in CAMPOS_TEXTO_IZQUIERDA:
                    celda.alignment = Alignment(horizontal="left", vertical="center")
                else:
                    celda.alignment = Alignment(horizontal="center", vertical="center")

                anchos[col_idx - 1] = max(anchos[col_idx - 1], len(_formatear_valor(usuario, campo)))

    for col_idx, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(min(ancho + 4, 35), 12)

    # Encabezado siempre visible al bajar, filtros por columna y hoja lista para imprimir.
    ws.freeze_panes = f"A{primera_fila_datos}"
    if usuarios:
        ws.auto_filter.ref = f"A{fila_encabezado}:{ultima_letra}{fila_encabezado + len(usuarios)}"
    ws.print_title_rows = f"{fila_encabezado}:{fila_encabezado}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


class _CanvasNumerado(canvas.Canvas):
    """Canvas que escribe 'Página X de Y' al pie (el total recién se conoce al terminar)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estados_paginas = []

    def showPage(self):
        self._estados_paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._estados_paginas)
        for estado in self._estados_paginas:
            self.__dict__.update(estado)
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#555555"))
            self.drawRightString(landscape(A4)[0] - 20, 12, f"Página {self._pageNumber} de {total}")
            super().showPage()
        super().save()


def generar_pdf_socios(
    usuarios: list[UsuarioFiltradoResponse],
    filtros: dict[str, str] | None = None,
) -> io.BytesIO:
    """Genera un archivo PDF en memoria con tabla apaisada de los socios filtrados."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=25,
        bottomMargin=25,
        title="GAMO - Listado de Socios Exportados",
    )
    elementos = []
    estilos = getSampleStyleSheet()
    texto_filtros = _texto_filtros(filtros)

    estilo_titulo = ParagraphStyle(
        "TituloPDF",
        parent=estilos["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1F497D"),
        spaceAfter=4,
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloPDF",
        parent=estilos["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4 if texto_filtros else 12,
    )
    estilo_filtros = ParagraphStyle(
        "FiltrosPDF",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1F497D"),
        spaceAfter=12,
    )

    elementos.append(Paragraph("GAMO - Listado de Socios Exportados", estilo_titulo))
    elementos.append(Paragraph(_subtitulo(len(usuarios)), estilo_subtitulo))
    if texto_filtros:
        elementos.append(Paragraph(escape(_texto_pdf(texto_filtros)), estilo_filtros))

    estilo_header = ParagraphStyle(
        "HeaderTabla",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    estilo_celda = ParagraphStyle(
        "CeldaTabla",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        alignment=1,
    )
    estilo_celda_izq = ParagraphStyle(
        "CeldaTablaIzq",
        parent=estilo_celda,
        alignment=0,
    )

    encabezados = [Paragraph(escape(titulo), estilo_header) for titulo, _ in COLUMNAS_EXPORTACION]
    datos_tabla = [encabezados]

    if not usuarios:
        fila_vacia = [
            Paragraph("No se encontraron socios para los filtros seleccionados.", estilo_celda)
        ] + [Paragraph("", estilo_celda) for _ in range(len(COLUMNAS_EXPORTACION) - 1)]
        datos_tabla.append(fila_vacia)
    else:
        for usuario in usuarios:
            fila = []
            for _, campo in COLUMNAS_EXPORTACION:
                texto = escape(_texto_pdf(_formatear_valor(usuario, campo)))
                estilo = estilo_celda_izq if campo in CAMPOS_TEXTO_IZQUIERDA else estilo_celda
                fila.append(Paragraph(texto, estilo))
            datos_tabla.append(fila)

    anchos_columnas = [55, 80, 80, 75, 110, 75, 68, 68, 65, 65, 60]
    comandos_estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F9")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]
    if not usuarios:
        comandos_estilo.append(("SPAN", (0, 1), (-1, 1)))

    tabla = Table(datos_tabla, colWidths=anchos_columnas, repeatRows=1)
    tabla.setStyle(TableStyle(comandos_estilo))

    elementos.append(tabla)
    doc.build(elementos, canvasmaker=_CanvasNumerado)
    buffer.seek(0)
    return buffer