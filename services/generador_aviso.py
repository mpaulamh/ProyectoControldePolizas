from fpdf import FPDF
from datetime import date

# Colores
ROJO_BANDA = (174, 24, 0)      # #AE1800
GRIS_PIE = (128, 128, 128)     # gris


def _latin1(texto):
    """Convierte texto a latin-1 para que las tildes no fallen en fpdf2."""
    if texto is None:
        return ""
    return str(texto).encode("latin-1", errors="replace").decode("latin-1")


def _fecha_str(fecha):
    """Devuelve una fecha en dd/mm/aaaa o 'No registrada' si es None."""
    if fecha is None:
        return "No registrada"
    if isinstance(fecha, date):
        return fecha.strftime("%d/%m/%Y")
    return str(fecha)


def _monto_str(monto):
    """Devuelve el monto formateado o 'No registrada' si es None."""
    if monto is None:
        return "No registrada"
    return f"{monto:,.2f}"


def crear_aviso_pdf(poliza):
    """Crea un aviso de renovación de póliza en PDF (A4 vertical) y lo devuelve en bytes."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Fuente Helvetica
    pdf.set_font("Helvetica", "", 12)

    # ---- Banda superior roja ----
    pdf.set_fill_color(*ROJO_BANDA)
    pdf.rect(0, 0, 210, 28, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, 8)
    pdf.cell(0, 7, _latin1("Corredora de Seguros Horizonte"), ln=True)
    pdf.set_xy(12, 17)
    pdf.cell(0, 7, _latin1("Aviso de renovación de póliza"), ln=True)
    pdf.set_text_color(0, 0, 0)

    # Espacio después de la banda
    pdf.ln(14)

    # ---- Saludo ----
    nombre = poliza.get("nombre") or "cliente"
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, _latin1(f"Estimado(a) {nombre}:"), ln=True)
    pdf.ln(5)

    # ---- Párrafo según estado ----
    estado = poliza.get("estado")
    hasta = poliza.get("hasta")
    dias = poliza.get("dias_hasta_vencer")
    asesor = poliza.get("asesor")

    if estado == "Vencida" and hasta is not None:
        pdf.multi_cell(
            0,
            7,
            _latin1(f"Su póliza venció el {_fecha_str(hasta)}. Por favor acérquese a nuestras oficinas para renovarla."),
        )
    elif estado == "Por vencer" and hasta is not None and dias is not None:
        pdf.multi_cell(
            0,
            7,
            _latin1(
                f"Su póliza vence el {_fecha_str(hasta)} en {dias} días. Su asesor ({asesor}) se comunicará con usted."
            ),
        )
    else:
        pdf.multi_cell(0, 7, _latin1("A continuación encontrará el detalle de su póliza:"))

    pdf.ln(6)

    # ---- Tabla de datos en filas ----
    ancho_etiqueta = 60
    ancho_valor = 120
    alto_fila = 8
    x_inicial = 12

    filas = [
        ("Número de póliza", poliza.get("numero") or "No registrada"),
        ("Aseguradora", poliza.get("aseguradora") or "No registrada"),
        ("Ramo", poliza.get("ramo") or "No registrada"),
        ("Cédula", poliza.get("cedula") or "No registrada"),
        (
            "Vigencia",
            f"{_fecha_str(poliza.get('desde'))} al {_fecha_str(poliza.get('hasta'))}",
        ),
        ("Prima anual", _monto_str(poliza.get("prima"))),
        ("Forma de pago", poliza.get("pago") or "No registrada"),
    ]

    pdf.set_x(x_inicial)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(ancho_etiqueta, alto_fila, _latin1("Campo"), border=1, align="C")
    pdf.cell(ancho_valor, alto_fila, _latin1("Valor"), border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for etiqueta, valor in filas:
        pdf.set_x(x_inicial)
        pdf.cell(ancho_etiqueta, alto_fila, _latin1(etiqueta), border=1)
        pdf.cell(ancho_valor, alto_fila, _latin1(valor), border=1)
        pdf.ln()
    pdf.ln(6)

    # ---- Pie de página gris ----
    pdf.set_y(-20)
    pdf.set_text_color(*GRIS_PIE)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(
        0,
        5,
        _latin1("Documento ficticio con fines académicos - Corredora de Seguros Horizonte"),
        align="C",
    )

    return bytes(pdf.output(dest="S"))