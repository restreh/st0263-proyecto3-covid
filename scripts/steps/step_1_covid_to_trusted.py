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

# Constants - Hadoop AWS packages for local Spark S3 access
# PySpark 4.0.1 uses Hadoop 3.4.0, so match that version
HADOOP_AWS_VERSION = "3.4.0"
AWS_SDK_VERSION = "1.12.367"


def create_spark_session(app_name: str):
    """
    Create Spark session with S3 support for local execution.

    For local development, includes Hadoop AWS and AWS SDK packages.
    For EMR, these packages are already available.

    Args:
        app_name: Name for the Spark application

    Returns:
        Configured SparkSession
    """
    builder = SparkSession.builder.appName(app_name)

    # Add AWS packages and configuration for local S3 access (not needed on EMR)
    if os.getenv("SPARK_LOCAL", "false").lower() == "true":
        builder = (
            builder.config(
                "spark.jars.packages",
                f"org.apache.hadoop:hadoop-aws:{HADOOP_AWS_VERSION},"
                f"com.amazonaws:aws-java-sdk-bundle:{AWS_SDK_VERSION}"
            )
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                    "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
        )

    return builder.getOrCreate()


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
    spark = create_spark_session("covid_raw_to_trusted")

    raw_covid_path = f"s3://{BUCKET}/{RAW_COVID_PREFIX}/casos_covid.csv"
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

    print(f"read: {df_demog.count()} demographics rows")

    # Normalize department names for join
    print("normalizing department names")
    df_covid = df_covid.withColumn(
        "departamento_nom_norm", upper(trim(col("departamento_nom")))
    )

    df_demog = df_demog.withColumn(
        "departamento_norm", upper(trim(col("departamento")))
    )

    # Join COVID data with demographics by normalized department name
    print("joining covid data with demographics")

    # Use aliases to avoid column name conflicts
    df_covid_aliased = df_covid.alias("covid")
    df_demog_aliased = df_demog.alias("demog")

    df_join = df_covid_aliased.join(
        df_demog_aliased,
        df_covid_aliased["departamento_nom_norm"] == df_demog_aliased["departamento_norm"],
        how="left",
    )

    print("join: done")

    # Parse dates and add partitioning columns
    print("adding date partitioning columns")
    df_join = (
        df_join.withColumn("fecha_reporte_web_date", to_date(col("covid.fecha_reporte_web")))
        .withColumn("anio", year(col("fecha_reporte_web_date")))
        .withColumn("mes", month(col("fecha_reporte_web_date")))
        .withColumn("dia", dayofmonth(col("fecha_reporte_web_date")))
    )

    # Select relevant columns from COVID data and demographics
    # Use explicit table aliases to avoid ambiguity
    print("selecting columns")
    df_trusted = df_join.select(
        # COVID columns from API
        col("covid.id_de_caso"),
        col("covid.fecha_reporte_web"),
        col("fecha_reporte_web_date"),
        col("covid.fecha_de_notificaci_n"),
        col("anio"),
        col("mes"),
        col("dia"),
        col("covid.departamento").alias("codigo_divipola_departamento"),  # DIVIPOLA code from COVID
        col("covid.departamento_nom"),  # Department name
        col("covid.ciudad_municipio"),  # DIVIPOLA municipality code
        col("covid.ciudad_municipio_nom"),  # Municipality name
        col("covid.edad"),
        col("covid.unidad_medida"),
        col("covid.sexo"),
        col("covid.fuente_tipo_contagio"),
        col("covid.ubicacion"),
        col("covid.estado"),
        col("covid.pais_viajo_1_cod"),
        col("covid.pais_viajo_1_nom"),
        col("covid.recuperado"),
        col("covid.fecha_inicio_sintomas"),
        col("covid.fecha_muerte"),
        col("covid.fecha_diagnostico"),
        col("covid.fecha_recuperado"),
        col("covid.tipo_recuperacion"),
        col("covid.per_etn_"),  # Ethnic group code
        col("covid.nom_grupo_"),  # Ethnic group name
        # Demographics columns (from join)
        col("demog.codigo_departamento"),  # From demographics CSV
        col("demog.departamento").alias("departamento_nombre"),  # Department name from demographics
        col("demog.poblacion"),  # From demographics CSV
    )

    print(f"selected: {len(df_trusted.columns)} columns")

    # Repartition to reduce number of output files and improve write performance
    print("repartitioning data")
    df_trusted = df_trusted.repartition(8, "anio", "mes", "dia")

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
