import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    coalesce,
    count,
    sum as Fsum,
    when,
    lit,
)
from pyspark.sql.window import Window

BUCKET = os.getenv("COVID_BUCKET_NAME", "st0263-proyecto3-covid19")
TRUSTED_COVID_PREFIX = "trusted/covid"
REFINED_INDICADORES_PREFIX = "refined/indicadores_departamento"


def main():
    spark = (
        SparkSession.builder
        .appName("covid_trusted_to_refined_indicadores_departamento")
        .getOrCreate()
    )

    trusted_path = f"s3://{BUCKET}/{TRUSTED_COVID_PREFIX}"
    print(f"Leyendo datos trusted desde: {trusted_path}")

    df = (
        spark.read
        .parquet(trusted_path)
    )

    print(f"Filas en trusted/covid: {df.count()}")

    # Normalizar código y nombre de departamento para agregaciones
    dept_code = coalesce(
        col("codigo_departamento").cast("string"),
        col("departamento").cast("string")
    ).alias("codigo_departamento_norm")

    dept_name = coalesce(
        col("nombre_departamento"),
        col("departamento_nom")
    ).alias("nombre_departamento_norm")

    df_norm = (
        df
        .withColumn("codigo_departamento_norm", dept_code)
        .withColumn("nombre_departamento_norm", dept_name)
    )

    # Usar población y región si están disponibles (pueden venir nulos para algunos)
    # Agregación diaria por departamento
    group_cols = [
        col("fecha_reporte_web_date").alias("fecha"),
        col("anio"),
        col("mes"),
        col("dia"),
        col("codigo_departamento_norm").alias("codigo_departamento"),
        col("nombre_departamento_norm").alias("nombre_departamento"),
        col("region"),
        col("poblacion"),
    ]

    df_daily = (
        df_norm
        .groupBy(*group_cols)
        .agg(
            count("*").alias("casos_nuevos")
        )
    )

    # Ventana para calcular acumulados por departamento en el tiempo
    w = Window.partitionBy("codigo_departamento").orderBy("fecha")

    df_daily = df_daily.withColumn(
        "casos_acumulados",
        Fsum(col("casos_nuevos")).over(w)
    )

    # Casos por 100.000 habitantes (si hay población disponible)
    df_daily = df_daily.withColumn(
        "casos_por_100k",
        when(
            (col("poblacion").isNotNull()) & (col("poblacion") > 0),
            (col("casos_acumulados") * lit(100000.0)) / col("poblacion")
        ).otherwise(lit(None))
    )

    # Orden lógico de columnas
    cols_final = [
        "fecha",
        "anio",
        "mes",
        "dia",
        "codigo_departamento",
        "nombre_departamento",
        "region",
        "poblacion",
        "casos_nuevos",
        "casos_acumulados",
        "casos_por_100k",
    ]

    df_final = df_daily.select(*cols_final)

    refined_path = f"s3://{BUCKET}/{REFINED_INDICADORES_PREFIX}"
    print(f"Escribiendo indicadores en: {refined_path}")

    (
        df_final
        .write
        .mode("overwrite")
        .partitionBy("anio", "mes", "dia")
        .parquet(refined_path)
    )

    print("Generación de indicadores por departamento completada.")
    spark.stop()


if __name__ == "__main__":
    main()
