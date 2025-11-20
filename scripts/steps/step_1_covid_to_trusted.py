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

# Bucket y prefijos
BUCKET = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
RAW_COVID_PREFIX = "raw/covid"
RAW_RDS_PREFIX = "raw/rds"
TRUSTED_COVID_PREFIX = "trusted/covid"


def main():
    spark = SparkSession.builder.appName("covid_raw_to_trusted").getOrCreate()

    raw_covid_path = f"s3://{BUCKET}/{RAW_COVID_PREFIX}/*.csv"
    raw_demog_path = f"s3://{BUCKET}/{RAW_RDS_PREFIX}/departamento_demografia.csv"

    print(f"Leyendo casos COVID desde: {raw_covid_path}")
    df_covid = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(raw_covid_path)
    )

    print(f"Filas COVID (raw): {df_covid.count()}")

    print(f"Lectura demografía desde: {raw_demog_path}")
    df_demog = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(raw_demog_path)
    )

    # Normalizar nombres de departamento en ambos lados
    # Campos típicos en dataset COVID: departamento, departamento_nom
    df_covid = df_covid.withColumn(
        "departamento_nom_norm", upper(trim(col("departamento_nom")))
    )

    df_demog = df_demog.withColumn(
        "nombre_departamento_norm", upper(trim(col("nombre_departamento")))
    )

    # Join por nombre normalizado
    df_join = df_covid.join(
        df_demog,
        df_covid.departamento_nom_norm == df_demog.nombre_departamento_norm,
        how="left",
    )

    # Cast y parse de fechas básicas
    # Ajusta los nombres si tu dataset trae variantes
    df_join = (
        df_join.withColumn("fecha_reporte_web_date", to_date(col("fecha_reporte_web")))
        .withColumn("anio", year(col("fecha_reporte_web_date")))
        .withColumn("mes", month(col("fecha_reporte_web_date")))
        .withColumn("dia", dayofmonth(col("fecha_reporte_web_date")))
    )

    # Seleccionar columnas relevantes + campos demográficos
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
        "nombre_departamento",
        "region",
        "poblacion",
        "anio_corte",
    ]

    df_trusted = df_join.select(*[c for c in columnas if c in df_join.columns])

    trusted_path = f"s3://{BUCKET}/{TRUSTED_COVID_PREFIX}"

    print(f"Escribiendo datos limpios en: {trusted_path}")
    (
        df_trusted.write.mode("overwrite")
        .partitionBy("anio", "mes", "dia")
        .parquet(trusted_path)
    )

    print("ETL raw → trusted completado.")
    spark.stop()


if __name__ == "__main__":
    main()
