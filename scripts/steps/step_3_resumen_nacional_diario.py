import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    sum as Fsum,
    max as Fmax,
    lit,
)

BUCKET = os.getenv("COVID_BUCKET_NAME", "st0263-proyecto3-covid19")

REFINED_INDICADORES_PREFIX = "refined/indicadores_departamento"
API_VIEW_PREFIX = "refined/api_views/resumen_nacional_diario"


def main():
    spark = (
        SparkSession.builder
        .appName("covid_resumen_nacional_diario")
        .getOrCreate()
    )

    indicadores_path = f"s3://{BUCKET}/{REFINED_INDICADORES_PREFIX}"
    print(f"Leyendo indicadores por departamento desde: {indicadores_path}")

    df = spark.read.parquet(indicadores_path)
    print(f"Filas en refined/indicadores_departamento: {df.count()}")

    # Agregación nacional diaria:
    # - suma de casos_nuevos
    # - suma de casos_acumulados
    # - suma de población (aprox para tasa nacional)
    # - casos_por_100k_nacional = (casos_acumulados_nacional * 100000) / poblacion_total
    df_nat = (
        df.groupBy("fecha", "anio", "mes", "dia")
        .agg(
            Fsum("casos_nuevos").alias("casos_nuevos_nacional"),
            Fsum("casos_acumulados").alias("casos_acumulados_nacional"),
            Fsum("poblacion").alias("poblacion_total_aprox")
        )
    )

    df_nat = df_nat.withColumn(
        "casos_por_100k_nacional",
        (col("casos_acumulados_nacional") * lit(100000.0)) / col("poblacion_total_aprox")
    )

    # Para conveniencia, agregamos la última fecha observada como campo redundante opcional
    ultima_fecha = df_nat.agg(Fmax("fecha").alias("ultima_fecha")).collect()[0]["ultima_fecha"]
    df_nat = df_nat.withColumn("ultima_fecha_disponible", lit(ultima_fecha))

    cols_final = [
        "fecha",
        "anio",
        "mes",
        "dia",
        "casos_nuevos_nacional",
        "casos_acumulados_nacional",
        "poblacion_total_aprox",
        "casos_por_100k_nacional",
        "ultima_fecha_disponible",
    ]

    df_final = df_nat.select(*cols_final)

    out_path = f"s3://{BUCKET}/{API_VIEW_PREFIX}"
    print(f"Escribiendo resumen nacional diario en: {out_path}")

    (
        df_final
        .write
        .mode("overwrite")
        .partitionBy("anio", "mes", "dia")
        .parquet(out_path)
    )

    print("Generación de vista resumen_nacional_diario completada.")
    spark.stop()


if __name__ == "__main__":
    main()
