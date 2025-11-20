import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    sum as Fsum,
    max as Fmax,
    lit,
)

# Constants - S3 paths
BUCKET = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
REFINED_INDICADORES_PREFIX = "refined/indicadores_departamento"
API_VIEW_PREFIX = "refined/api_views/resumen_nacional_diario"


def main():
    """
    Generate national-level daily COVID summary from department indicators.

    Steps:
    1. Read department indicators
    2. Aggregate to national level by date
    3. Calculate national cases per 100k population
    4. Write summary to refined zone for API consumption
    """
    spark = SparkSession.builder.appName("covid_resumen_nacional_diario").getOrCreate()

    indicadores_path = f"s3://{BUCKET}/{REFINED_INDICADORES_PREFIX}"
    print(f"reading department indicators from {indicadores_path}")

    df = spark.read.parquet(indicadores_path)
    print(f"read: {df.count()} rows from refined/indicadores_departamento")

    # Aggregate to national level by date
    print("aggregating to national level")
    df_nat = df.groupBy("fecha", "anio", "mes", "dia").agg(
        Fsum("casos_nuevos").alias("casos_nuevos_nacional"),
        Fsum("casos_acumulados").alias("casos_acumulados_nacional"),
        Fsum("poblacion").alias("poblacion_total_aprox"),
    )

    print("aggregation: done")

    # Calculate national cases per 100k population
    print("calculating national cases per 100k")
    df_nat = df_nat.withColumn(
        "casos_por_100k_nacional",
        (col("casos_acumulados_nacional") * lit(100000.0))
        / col("poblacion_total_aprox"),
    )

    # Add latest available date for convenience
    print("finding latest date")
    ultima_fecha = df_nat.agg(Fmax("fecha").alias("ultima_fecha")).collect()[0][
        "ultima_fecha"
    ]
    df_nat = df_nat.withColumn("ultima_fecha_disponible", lit(ultima_fecha))

    print(f"latest date: {ultima_fecha}")

    # Select final columns
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

    print(f"selected: {len(df_final.columns)} columns")

    out_path = f"s3://{BUCKET}/{API_VIEW_PREFIX}"
    print(f"writing national summary to {out_path}")

    (
        df_final.write.mode("overwrite")
        .partitionBy("anio", "mes", "dia")
        .parquet(out_path)
    )

    print("write: done")
    print("national daily summary: done")
    spark.stop()


if __name__ == "__main__":
    main()
