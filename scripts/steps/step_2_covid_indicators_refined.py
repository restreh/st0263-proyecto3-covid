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

# Constants - S3 paths
BUCKET = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
TRUSTED_COVID_PREFIX = "trusted/covid"
REFINED_INDICADORES_PREFIX = "refined/indicadores_departamento"


def main():
    """
    Generate department-level COVID indicators from trusted data.

    Steps:
    1. Read trusted COVID data
    2. Normalize department codes and names
    3. Aggregate daily cases by department
    4. Calculate cumulative cases using window functions
    5. Calculate cases per 100k population
    6. Write indicators to refined zone
    """
    spark = SparkSession.builder.appName(
        "covid_trusted_to_refined_indicadores_departamento"
    ).getOrCreate()

    trusted_path = f"s3://{BUCKET}/{TRUSTED_COVID_PREFIX}"
    print(f"reading trusted data from {trusted_path}")

    df = spark.read.parquet(trusted_path)

    print(f"read: {df.count()} rows from trusted/covid")

    # Normalize department code and name for aggregations
    print("normalizing department fields")
    dept_code = coalesce(
        col("codigo_departamento").cast("string"), col("departamento").cast("string")
    ).alias("codigo_departamento_norm")

    dept_name = coalesce(col("departamento"), col("departamento_nom")).alias(
        "nombre_departamento_norm"
    )

    df_norm = df.withColumn("codigo_departamento_norm", dept_code).withColumn(
        "nombre_departamento_norm", dept_name
    )

    # Aggregate daily cases by department
    print("aggregating daily cases by department")
    group_cols = [
        col("fecha_reporte_web_date").alias("fecha"),
        col("anio"),
        col("mes"),
        col("dia"),
        col("codigo_departamento_norm").alias("codigo_departamento"),
        col("nombre_departamento_norm").alias("nombre_departamento"),
        col("poblacion"),
    ]

    df_daily = df_norm.groupBy(*group_cols).agg(count("*").alias("casos_nuevos"))

    print("aggregation: done")

    # Calculate cumulative cases using window function
    print("calculating cumulative cases")
    w = Window.partitionBy("codigo_departamento").orderBy("fecha")

    df_daily = df_daily.withColumn(
        "casos_acumulados", Fsum(col("casos_nuevos")).over(w)
    )

    # Calculate cases per 100k population
    print("calculating cases per 100k population")
    df_daily = df_daily.withColumn(
        "casos_por_100k",
        when(
            (col("poblacion").isNotNull()) & (col("poblacion") > 0),
            (col("casos_acumulados") * lit(100000.0)) / col("poblacion"),
        ).otherwise(lit(None)),
    )

    # Select final columns
    cols_final = [
        "fecha",
        "anio",
        "mes",
        "dia",
        "codigo_departamento",
        "nombre_departamento",
        "poblacion",
        "casos_nuevos",
        "casos_acumulados",
        "casos_por_100k",
    ]

    df_final = df_daily.select(*cols_final)

    print(f"selected: {len(df_final.columns)} columns")

    refined_path = f"s3://{BUCKET}/{REFINED_INDICADORES_PREFIX}"
    print(f"writing indicators to {refined_path}")

    (
        df_final.write.mode("overwrite")
        .partitionBy("anio", "mes", "dia")
        .parquet(refined_path)
    )

    print("write: done")
    print("department indicators: done")
    spark.stop()


if __name__ == "__main__":
    main()
