from datetime import date
from models.datos import cargar_clientes, cargar_polizas

# Reglas del negocio
FECHA_CORTE = date(2026, 11, 9)
DIAS_AVISO = 30


def estado_poliza(hasta, fecha_corte=FECHA_CORTE):
    """Devuelve el estado de una póliza según su fecha de vigencia hasta."""
    if hasta is None:
        return "Sin fecha"
    dias = (hasta - fecha_corte).days
    if hasta < fecha_corte:
        return "Vencida"
    elif 0 <= dias <= DIAS_AVISO:
        return "Por vencer"
    else:
        return "Vigente"


def calcular_resultados(fecha_corte=FECHA_CORTE):
    """Cruza pólizas con el maestro por cédula y devuelve lista ordenada por urgencia."""
    clientes = cargar_clientes()
    polizas = cargar_polizas()

    # Índice de clientes por cédula para cruce rápido
    clientes_por_cedula = {}
    for _, fila in clientes.iterrows():
        cedula = str(fila["Cedula"]).strip()
        clientes_por_cedula[cedula] = {
            "correo": fila.get("Correo"),
            "nombre": fila.get("Nombre_Completo"),
        }

    resultados = []
    for poliza in polizas:
        cedula = poliza.get("cedula")
        info_cliente = clientes_por_cedula.get(cedula)
        en_maestro = info_cliente is not None

        hasta = poliza.get("hasta")
        estado = estado_poliza(hasta, fecha_corte)
        if hasta is not None:
            dias_hasta_vencer = (hasta - fecha_corte).days
        else:
            dias_hasta_vencer = None

        resultados.append({
            "numero": poliza.get("numero"),
            "aseguradora": poliza.get("aseguradora"),
            "ramo": poliza.get("ramo"),
            "nombre": poliza.get("nombre"),
            "cedula": cedula,
            "correo": info_cliente["correo"] if en_maestro else None,
            "en_maestro": en_maestro,
            "desde": poliza.get("desde"),
            "hasta": hasta,
            "prima": poliza.get("prima"),
            "pago": poliza.get("pago"),
            "suma": poliza.get("suma"),
            "asesor": poliza.get("asesor"),
            "archivo": poliza.get("archivo"),
            "dias_hasta_vencer": dias_hasta_vencer,
            "estado": estado,
        })

    # Ordenar de menos a más días (lo urgente primero); los None van al final
    resultados.sort(key=lambda r: (r["dias_hasta_vencer"] is None, r["dias_hasta_vencer"] or 0))
    return resultados


def contar_por_estado(resultados):
    """Cuenta cuántas pólizas hay de cada estado."""
    conteo = {"Vigente": 0, "Por vencer": 0, "Vencida": 0, "Sin fecha": 0}
    for r in resultados:
        estado = r["estado"]
        if estado in conteo:
            conteo[estado] += 1
        else:
            conteo[estado] = 1
    return conteo


def primas_por_aseguradora(resultados):
    """Suma primas de pólizas no vencidas por aseguradora, de mayor a menor."""
    sumas = {}
    for r in resultados:
        if r["estado"] == "Vencida":
            continue
        aseguradora = r["aseguradora"]
        prima = r["prima"] if r["prima"] is not None else 0
        sumas[aseguradora] = sumas.get(aseguradora, 0) + prima
    # Ordenar de mayor a menor
    return dict(sorted(sumas.items(), key=lambda x: x[1], reverse=True))


def buscar_inconsistencias(resultados):
    """Detecta los 3 tipos de inconsistencia descritos en AGENTS.md."""
    clientes = cargar_clientes()
    polizas = cargar_polizas()

    # Cedulas que aparecen en los resultados
    cedulas_en_polizas = {r["cedula"] for r in resultados if r["cedula"] is not None}

    inconsistencias = []

    # (1) Cliente del maestro sin ninguna póliza
    for _, fila in clientes.iterrows():
        cedula = str(fila["Cedula"]).strip()
        if cedula not in cedulas_en_polizas:
            inconsistencias.append(
                f"Cliente sin póliza: cédula {cedula} ({fila.get('Nombre_Completo')}) no tiene ninguna póliza."
            )

    # (2) Póliza cuya cédula no está en el maestro
    for r in resultados:
        if not r["en_maestro"]:
            inconsistencias.append(
                f"Cédula no registrada: póliza {r['numero']} con cédula {r['cedula']} no está en el maestro."
            )

    # (3) Póliza sin prima o con fecha ilegible
    for r in resultados:
        if r["prima"] is None or r["desde"] is None or r["hasta"] is None:
            inconsistencias.append(
                f"Datos incompletos: póliza {r['numero']} sin prima o fecha ilegible."
            )

    return inconsistencias


def buscar_por_numero(numero, resultados=None):
    """Busca una póliza por su número en la lista de resultados."""
    if resultados is None:
        resultados = calcular_resultados()
    for r in resultados:
        if r["numero"] == numero:
            return r
    return None