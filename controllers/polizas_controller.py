from flask import Blueprint, render_template, send_file, abort, request, flash, redirect, url_for
from io import BytesIO
import zipfile
import os
import pandas as pd

from models.polizas import (
    calcular_resultados,
    buscar_por_numero,
    FECHA_CORTE,
)
from services.generador_aviso import crear_aviso_pdf
from models.datos import CLIENTES_PATH, cargar_clientes

polizas_bp = Blueprint("polizas", __name__)


@polizas_bp.route("/")
def inicio():
    """Tablero principal: muestra resultados, conteo, primas, inconsistencias y fecha de corte."""
    resultados = calcular_resultados()

    from models.polizas import contar_por_estado, primas_por_aseguradora, buscar_inconsistencias

    conteo = contar_por_estado(resultados)
    primas = primas_por_aseguradora(resultados)
    inconsistencias = buscar_inconsistencias(resultados)

    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=conteo,
        primas=primas,
        inconsistencias=inconsistencias,
        fecha_corte=FECHA_CORTE.strftime("%d/%m/%Y"),
    )


@polizas_bp.route("/importar-clientes", methods=["POST"])
def importar_clientes():
    """Importa un archivo Excel nuevo de clientes (reemplaza Maestro_Clientes.xlsx)."""
    if "archivo" not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("polizas.inicio"))

    archivo = request.files["archivo"]
    if archivo.filename == "":
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("polizas.inicio"))

    if not (archivo.filename.endswith(".xlsx") or archivo.filename.endswith(".xls")):
        flash("Solo se permiten archivos Excel (.xlsx o .xls).", "error")
        return redirect(url_for("polizas.inicio"))

    try:
        # Validar que sea un Excel legible con la hoja Clientes
        df = pd.read_excel(archivo, sheet_name="Clientes")
        if "Cedula" not in df.columns:
            flash("El Excel debe contener una columna llamada 'Cedula'.", "error")
            return redirect(url_for("polizas.inicio"))

        # Guardar sobre el archivo existente en la bodega de datos
        archivo.save(CLIENTES_PATH)

        flash("Clientes importados correctamente desde " + archivo.filename, "exito")
    except Exception as e:
        flash(f"Error al importar el Excel: {str(e)}", "error")

    return redirect(url_for("polizas.inicio"))


@polizas_bp.route("/procesar", methods=["POST"])
def procesar():
    """Ejecuta el proceso de cálculo de estados, conteos, primas e inconsistencias."""
    try:
        resultados = calcular_resultados()
        total = len(resultados)
        flash(f"Proceso generado correctamente. {total} póliza(s) procesada(s).", "exito")
    except Exception as e:
        flash(f"Error al generar el proceso: {str(e)}", "error")

    return redirect(url_for("polizas.inicio"))


@polizas_bp.route("/aviso/")
def aviso():
    """Devuelve el PDF de aviso de una póliza para verlo en el navegador."""
    numero = request.args.get("numero")
    if not numero:
        abort(404)

    resultados = calcular_resultados()
    poliza = buscar_por_numero(numero, resultados)

    if poliza is None:
        abort(404)

    if poliza["estado"] == "Vigente":
        abort(404)

    pdf_bytes = crear_aviso_pdf(poliza)

    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"aviso_{numero}.pdf",
    )


@polizas_bp.route("/descargar-avisos")
def descargar_avisos():
    """Arma en memoria un .zip con los avisos de pólizas Por vencer y Vencidas."""
    resultados = calcular_resultados()

    avisos = [r for r in resultados if r["estado"] in ("Por vencer", "Vencida")]

    if not avisos:
        flash("No hay pólizas por vencer o vencidas para exportar.", "error")
        return redirect(url_for("polizas.inicio"))

    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for r in avisos:
            pdf_bytes = crear_aviso_pdf(r)
            zf.writestr(f"aviso_{r['numero']}.pdf", pdf_bytes)

    mem_zip.seek(0)
    return send_file(
        mem_zip,
        mimetype="application/zip",
        as_attachment=True,
        download_name="avisos.zip",
    )