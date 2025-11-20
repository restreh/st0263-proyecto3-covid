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
            builder.master("local[2]")  # Use only 2 cores to reduce memory pressure
            .config(
                "spark.jars.packages",
                f"org.apache.hadoop:hadoop-aws:{HADOOP_AWS_VERSION},"
                f"com.amazonaws:aws-java-sdk-bundle:{AWS_SDK_VERSION}"
            )
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                    "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.driver.host", "localhost")
            .config("spark.driver.memory", "4g")  # Increase driver memory
            .config("spark.sql.shuffle.partitions", "8")  # Reduce shuffle partitions
            .config("spark.sql.files.maxPartitionBytes", "128MB")  # Smaller partition size
            .config("spark.default.parallelism", "8")  # Reduce parallelism
        )

    return builder.getOrCreate()


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
    spark = create_spark_session("covid_trusted_to_refined_indicadores_departamento")

    trusted_path = f"s3://{BUCKET}/{TRUSTED_COVID_PREFIX}"
    print(f"reading trusted data from {trusted_path}")

    df = spark.read.parquet(trusted_path)

    print(f"read: {df.count()} rows from trusted/covid")

    # Use DIVIPOLA department code and standardized name from demographics
    # The trusted zone has both the original COVID name and the normalized demographics name
    print("preparing department fields for aggregation")
    df_norm = df.withColumn(
        "codigo_departamento_norm",
        coalesce(
            col("codigo_departamento").cast("string"),
            col("codigo_divipola_departamento").cast("string")
        )
    ).withColumn(
        "nombre_departamento_norm",
        coalesce(col("departamento_nombre_normalizado"), col("departamento_nom"))
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
