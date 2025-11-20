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
    Generate national-level daily COVID summary from department indicators.

    Steps:
    1. Read department indicators
    2. Aggregate to national level by date
    3. Calculate national cases per 100k population
    4. Write summary to refined zone for API consumption
    """
    spark = create_spark_session("covid_resumen_nacional_diario")

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
