from flask import Blueprint, render_template, send_file, abort, request
from io import BytesIO
import zipfile

from models.polizas import (
    calcular_resultados,
    buscar_por_numero,
    FECHA_CORTE,
)
from services.generador_aviso import crear_aviso_pdf

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