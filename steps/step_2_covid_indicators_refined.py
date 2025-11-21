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
TRUSTED_COVID_PREFIX = "lake/trusted/covid"
REFINED_INDICADORES_PREFIX = "lake/refined/indicadores_departamento"
REFINED_ANALYTICS_PREFIX = "lake/refined/analytics"

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

    print(f"read: {df.count()} rows from lake/trusted/covid")

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

    # Run SparkSQL analytics before writing (optional, can be disabled with env var)
    if os.getenv("RUN_SQL_ANALYTICS", "true").lower() == "true":
        print("running sparksql analytics (saving results to refined/analytics)")

        # Register DataFrames as temporary SQL views
        df_norm.createOrReplaceTempView("covid_casos")
        df_final.createOrReplaceTempView("indicadores_diarios")

        # Query 1: Top 10 departments by cumulative cases per 100k (latest date)
        print("query 1: top 10 departments by case rate")
        df_top_depts = spark.sql("""
            WITH latest_data AS (
                SELECT
                    codigo_departamento,
                    nombre_departamento,
                    casos_por_100k,
                    casos_acumulados,
                    fecha,
                    ROW_NUMBER() OVER (PARTITION BY codigo_departamento ORDER BY fecha DESC) as rn
                FROM indicadores_diarios
                WHERE casos_por_100k IS NOT NULL
            )
            SELECT
                nombre_departamento,
                CAST(casos_por_100k AS DECIMAL(10,2)) as tasa_por_100k,
                casos_acumulados as casos_totales,
                fecha as ultima_actualizacion
            FROM latest_data
            WHERE rn = 1
            ORDER BY casos_por_100k DESC
            LIMIT 10
        """)
        df_top_depts.show(truncate=False)

        analytics_path_1 = f"s3://{BUCKET}/{REFINED_ANALYTICS_PREFIX}/top_departamentos_tasa"
        print(f"writing to {analytics_path_1}")
        df_top_depts.write.mode("overwrite").parquet(analytics_path_1)

        # Query 2: Monthly case trends with year-over-year comparison
        print("\nquery 2: monthly trends by year")
        df_monthly = spark.sql("""
            SELECT
                anio,
                mes,
                SUM(casos_nuevos) as casos_mensuales,
                COUNT(DISTINCT codigo_departamento) as departamentos_afectados,
                ROUND(AVG(casos_nuevos), 2) as promedio_diario
            FROM indicadores_diarios
            GROUP BY anio, mes
            ORDER BY anio, mes
        """)
        df_monthly.show(24, truncate=False)

        analytics_path_2 = f"s3://{BUCKET}/{REFINED_ANALYTICS_PREFIX}/tendencias_mensuales"
        print(f"writing to {analytics_path_2}")
        df_monthly.write.mode("overwrite").parquet(analytics_path_2)

        # Query 3: Age group distribution from raw cases
        print("\nquery 3: age group distribution of cases")
        df_age_groups = spark.sql("""
            SELECT
                CASE
                    WHEN edad < 18 THEN '0-17 años'
                    WHEN edad BETWEEN 18 AND 29 THEN '18-29 años'
                    WHEN edad BETWEEN 30 AND 49 THEN '30-49 años'
                    WHEN edad BETWEEN 50 AND 64 THEN '50-64 años'
                    WHEN edad >= 65 THEN '65+ años'
                    ELSE 'Desconocido'
                END as grupo_edad,
                COUNT(*) as total_casos,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
            FROM covid_casos
            WHERE edad IS NOT NULL
            GROUP BY
                CASE
                    WHEN edad < 18 THEN '0-17 años'
                    WHEN edad BETWEEN 18 AND 29 THEN '18-29 años'
                    WHEN edad BETWEEN 30 AND 49 THEN '30-49 años'
                    WHEN edad BETWEEN 50 AND 64 THEN '50-64 años'
                    WHEN edad >= 65 THEN '65+ años'
                    ELSE 'Desconocido'
                END
            ORDER BY total_casos DESC
        """)
        df_age_groups.show(truncate=False)

        analytics_path_3 = f"s3://{BUCKET}/{REFINED_ANALYTICS_PREFIX}/distribucion_edad"
        print(f"writing to {analytics_path_3}")
        df_age_groups.write.mode("overwrite").parquet(analytics_path_3)

        # Query 4: Gender breakdown with outcomes
        print("\nquery 4: gender distribution and outcomes")
        df_gender = spark.sql("""
            SELECT
                COALESCE(sexo, 'No reportado') as sexo,
                COUNT(*) as total_casos,
                SUM(CASE WHEN estado = 'Fallecido' THEN 1 ELSE 0 END) as fallecidos,
                SUM(CASE WHEN recuperado = 'Recuperado' THEN 1 ELSE 0 END) as recuperados,
                ROUND(SUM(CASE WHEN estado = 'Fallecido' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tasa_letalidad
            FROM covid_casos
            GROUP BY sexo
            ORDER BY total_casos DESC
        """)
        df_gender.show(truncate=False)

        analytics_path_4 = f"s3://{BUCKET}/{REFINED_ANALYTICS_PREFIX}/desglose_genero"
        print(f"writing to {analytics_path_4}")
        df_gender.write.mode("overwrite").parquet(analytics_path_4)

        # Query 5: Departments that reached 1000 cumulative cases (milestone analysis)
        print("\nquery 5: first date each department reached 1000 cases")
        df_milestones = spark.sql("""
            WITH milestone_dates AS (
                SELECT
                    codigo_departamento,
                    nombre_departamento,
                    fecha,
                    casos_acumulados,
                    CASE WHEN casos_acumulados >= 1000 THEN 1 ELSE 0 END as reached_milestone
                FROM indicadores_diarios
            ),
            first_milestone AS (
                SELECT
                    codigo_departamento,
                    nombre_departamento,
                    MIN(fecha) as fecha_milestone_1000
                FROM milestone_dates
                WHERE reached_milestone = 1
                GROUP BY codigo_departamento, nombre_departamento
            )
            SELECT
                nombre_departamento,
                fecha_milestone_1000,
                DATEDIFF(fecha_milestone_1000, '2020-03-06') as dias_desde_primer_caso
            FROM first_milestone
            ORDER BY fecha_milestone_1000
        """)
        df_milestones.show(15, truncate=False)

        analytics_path_5 = f"s3://{BUCKET}/{REFINED_ANALYTICS_PREFIX}/hitos_1000_casos"
        print(f"writing to {analytics_path_5}")
        df_milestones.write.mode("overwrite").parquet(analytics_path_5)

        # Query 6: Weekly moving average of new cases (smoothing)
        print("\nquery 6: 7-day moving average of national daily cases")
        df_moving_avg = spark.sql("""
            SELECT
                fecha,
                SUM(casos_nuevos) as casos_nuevos_nacional,
                ROUND(AVG(SUM(casos_nuevos)) OVER (
                    ORDER BY fecha
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ), 2) as promedio_movil_7dias
            FROM indicadores_diarios
            GROUP BY fecha
            ORDER BY fecha DESC
        """)
        df_moving_avg.show(30, truncate=False)

        analytics_path_6 = f"s3://{BUCKET}/{REFINED_ANALYTICS_PREFIX}/promedio_movil_7dias"
        print(f"writing to {analytics_path_6}")
        df_moving_avg.write.mode("overwrite").parquet(analytics_path_6)

        print("sparksql analytics: done (6 datasets saved)")

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
