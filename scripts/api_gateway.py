import json
import boto3
import time

athena = boto3.client("athena")

DATABASE = "refined_api_views"   # e.g., refined
OUTPUT = "s3://jacostaa1datalake/athena_results/"  # must exist!


def lambda_handler(event, context):
    print("EVENT:", event)

    path = event.get("rawPath") or event.get("path") or ""
    params = event.get("pathParameters") or {}

    if path == "/nacional/resumen":
        return get_national_summary()

    if path.startswith("/nacional/por-fecha/"):
        fecha = params.get("fecha")
        return get_national_by_date(fecha)

    if path == "/nacional/historico":
        return get_national_history()

    return respond(404, {"error": "Route not found"})


# -------------------------------------------------------
# ATHENA UTILITIES
# -------------------------------------------------------

def run_query(query):
    execution = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": OUTPUT}
    )

    query_id = execution["QueryExecutionId"]

    while True:
        status = athena.get_query_execution(QueryExecutionId=query_id)
        state = status["QueryExecution"]["Status"]["State"]
        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        time.sleep(0.3)

    if state != "SUCCEEDED":
        raise Exception(f"Athena query failed: {state}")

    return athena.get_query_results(QueryExecutionId=query_id)


def parse_results(results):
    rows = []
    for r in results["ResultSet"]["Rows"]:
        rows.append([c.get("VarCharValue") for c in r["Data"]])
    return rows


# -------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------

def get_national_summary():
    """
    Latest record from the national dataset.
    """
    query = """
        SELECT fecha,
               casos_nuevos_nacional,
               casos_acumulados_nacional,
               poblacion_total_aprox,
               casos_por_100k_nacional,
               ultima_fecha_disponible
        FROM resumen_nacional_diario
        ORDER BY fecha DESC
        LIMIT 1;
    """
    rows = parse_results(run_query(query))
    return respond(200, {"nacional_resumen": rows})


def get_national_by_date(fecha):
    """
    Returns national statistics for a specific date.
    Uses partitions anio, mes, dia.
    """
    y, m, d = fecha.split("-")

    query = f"""
        SELECT fecha,
               casos_nuevos_nacional,
               casos_acumulados_nacional,
               poblacion_total_aprox,
               casos_por_100k_nacional,
               ultima_fecha_disponible
        FROM resumen_nacional_diario
        WHERE anio = '{y}' AND mes = '{m}' AND dia = '{d}'
        LIMIT 1;
    """

    rows = parse_results(run_query(query))
    return respond(200, {"nacional_por_fecha": rows})


def get_national_history():
    """
    Returns a complete time series of national COVID data.
    """
    query = """
        SELECT fecha,
               casos_nuevos_nacional,
               casos_acumulados_nacional,
               poblacion_total_aprox,
               casos_por_100k_nacional
        FROM resumen_nacional_diario
        ORDER BY fecha ASC;
    """

    rows = parse_results(run_query(query))
    return respond(200, {"nacional_historico": rows})


# -------------------------------------------------------
# RESPONSE
# -------------------------------------------------------

def respond(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
