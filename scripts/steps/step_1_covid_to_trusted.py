import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    upper,
    trim,
    to_date,
    year,
    month,
    dayofmonth,
)

# Constants - S3 paths
BUCKET = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
RAW_COVID_PREFIX = "raw/covid"
RAW_RDS_PREFIX = "raw/rds"
TRUSTED_COVID_PREFIX = "trusted/covid"


def main():
    """
    Transform raw COVID data to trusted zone with demographic enrichment.

    Steps:
    1. Read raw COVID cases from S3
    2. Read demographic data from S3
    3. Join datasets by normalized department name
    4. Add date partitioning columns
    5. Write cleaned data to trusted zone as Parquet
    """
    spark = SparkSession.builder.appName("covid_raw_to_trusted").getOrCreate()

    raw_covid_path = f"s3://{BUCKET}/{RAW_COVID_PREFIX}/*.csv"
    raw_demog_path = f"s3://{BUCKET}/{RAW_RDS_PREFIX}/poblacion.csv"

    print(f"reading covid cases from {raw_covid_path}")
    df_covid = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(raw_covid_path)
    )

    print(f"read: {df_covid.count()} covid rows")

    print(f"reading demographics from {raw_demog_path}")
    df_demog = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(raw_demog_path)
    )

    print("read: demographics loaded")

    # Normalize department names for join
    print("normalizing department names")
    df_covid = df_covid.withColumn(
        "departamento_nom_norm", upper(trim(col("departamento_nom")))
    )

    df_demog = df_demog.withColumn(
        "departamento_norm", upper(trim(col("departamento")))
    )

    # Join COVID data with demographics
    print("joining covid data with demographics")
    df_join = df_covid.join(
        df_demog,
        df_covid.departamento_nom_norm == df_demog.departamento_norm,
        how="left",
    )

    print("join: done")

    # Parse dates and add partitioning columns
    print("adding date partitioning columns")
    df_join = (
        df_join.withColumn("fecha_reporte_web_date", to_date(col("fecha_reporte_web")))
        .withColumn("anio", year(col("fecha_reporte_web_date")))
        .withColumn("mes", month(col("fecha_reporte_web_date")))
        .withColumn("dia", dayofmonth(col("fecha_reporte_web_date")))
    )

    # Select relevant columns
    columnas = [
        "id_de_caso",
        "fecha_reporte_web_date",
        "anio",
        "mes",
        "dia",
        "departamento",
        "departamento_nom",
        "ciudad_municipio",
        "ciudad_municipio_nom",
        "edad",
        "unidad_medida",
        "sexo",
        "fuente_tipo_contagio",
        "ubicacion",
        "estado",
        "recuperado",
        "fecha_muerte",
        "fecha_recuperado",
        "codigo_departamento",
        "departamento",
        "poblacion",
    ]

    df_trusted = df_join.select(*[c for c in columnas if c in df_join.columns])

    print(f"selected: {len(df_trusted.columns)} columns")

    trusted_path = f"s3://{BUCKET}/{TRUSTED_COVID_PREFIX}"

    print(f"writing to {trusted_path}")
    (
        df_trusted.write.mode("overwrite")
        .partitionBy("anio", "mes", "dia")
        .parquet(trusted_path)
    )

    print("write: done")
    print("etl raw to trusted: done")
    spark.stop()


if __name__ == "__main__":
    main()
