import os
import pdfplumber
import pandas as pd
from datetime import datetime

# Carpetas de insumos (bodega de solo lectura)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Insumos_Control_Polizas")
CLIENTES_PATH = os.path.join(DATA_DIR, "Maestro_Clientes.xlsx")
POLIZAS_DIR = os.path.join(DATA_DIR, "polizas")

# Mapeo de etiquetas del PDF -> nombre de campo interno
CAMPOS = {
    "Numero de poliza": "numero",
    "Ramo": "ramo",
    "Tomador / Asegurado": "nombre",
    "Cedula": "cedula",
    "Vigencia desde": "desde",
    "Vigencia hasta": "hasta",
    "Prima anual": "prima",
    "Forma de pago": "pago",
    "Suma asegurada": "suma",
    "Asesor": "asesor",
}


def _fecha(texto):
    """Convierte un texto dd/mm/aaaa a objeto date. Devuelve None si está vacío."""
    if not texto or not texto.strip():
        return None
    return datetime.strptime(texto.strip(), "%d/%m/%Y").date()


def _monto(texto):
    """Convierte un monto tipo 'CRC 228,000.00' a número. Devuelve None si está vacío."""
    if not texto or not texto.strip():
        return None
    limpio = texto.strip().replace("CRC", "").replace(",", "").strip()
    if not limpio:
        return None
    return float(limpio)


def cargar_clientes():
    """Lee el Excel de clientes y devuelve un DataFrame con Cedula como texto sin espacios."""
    df = pd.read_excel(CLIENTES_PATH, sheet_name="Clientes", dtype={"Cedula": str})
    df["Cedula"] = df["Cedula"].str.strip()
    return df


def leer_poliza(ruta_pdf):
    """Lee un PDF de póliza y devuelve un diccionario con sus campos."""
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]
        texto = pagina.extract_text() or ""

    lineas = texto.splitlines()
    if not lineas:
        return None

    # Primera línea: nombre de la aseguradora
    aseguradora = lineas[0].strip()

    datos = {
        "archivo": os.path.basename(ruta_pdf),
        "aseguradora": aseguradora,
        "numero": None,
        "ramo": None,
        "nombre": None,
        "cedula": None,
        "desde": None,
        "hasta": None,
        "prima": None,
        "pago": None,
        "suma": None,
        "asesor": None,
    }

    # Recorrer las demás líneas con un bucle
    for linea in lineas[1:]:
        if ":" not in linea:
            continue
        etiqueta, valor = linea.split(":", 1)
        etiqueta = etiqueta.strip()
        valor = valor.strip()
        campo = CAMPOS.get(etiqueta)
        if campo is None:
            continue
        if campo in ("desde", "hasta"):
            datos[campo] = _fecha(valor)
        elif campo in ("prima", "suma"):
            datos[campo] = _monto(valor)
        else:
            datos[campo] = valor

    return datos


def cargar_polizas():
    """Recorre data/polizas en orden alfabético y devuelve una lista de diccionarios."""
    archivos = sorted(
        f for f in os.listdir(POLIZAS_DIR) if f.lower().endswith(".pdf")
    )
    polizas = []
    for archivo in archivos:
        ruta = os.path.join(POLIZAS_DIR, archivo)
        poliza = leer_poliza(ruta)
        if poliza is not None:
            polizas.append(poliza)
    return polizas