import os

import requests
import boto3

# Endpoint CSV del dataset de casos positivos de COVID-19 en Colombia (Datos Abiertos)
DATASET_URL = "https://www.datos.gov.co/resource/gt2j-8ykr.csv?$limit=5000000"

# Nombre del bucket S3
# Usa la variable de entorno COVID_BUCKET_NAME si existe,
# de lo contrario usa el bucket por defecto del proyecto.
BUCKET_NAME = os.getenv("COVID_BUCKET_NAME", "st0263-proyecto3-covid19")

# Prefijo dentro de la zona raw del bucket
RAW_PREFIX = "raw/covid"


def download_covid_csv() -> bytes:
    """
    Descarga el CSV completo del dataset de COVID-19 desde Datos Abiertos
    y devuelve el contenido en bytes.
    """
    print(f"Descargando datos desde {DATASET_URL} ...")
    response = requests.get(DATASET_URL, timeout=120)
    response.raise_for_status()
    print("Descarga completada.")
    return response.content


def upload_to_s3(data: bytes, bucket: str, key: str) -> None:
    """
    Sube el contenido 'data' al bucket y key indicados en S3.
    """
    print(f"Subiendo archivo a s3://{bucket}/{key} ...")
    s3 = boto3.client("s3")
    s3.put_object(Bucket=bucket, Key=key, Body=data)
    print("Carga en S3 completada.")


def main() -> None:
    """
    Downloads the COVID cases file from the API and uploads it to an S3 bucket.
    """
    object_key = f"{RAW_PREFIX}/casos_covid.csv"

    print("=== Ingesta dataset COVID-19 → S3 (zona raw) ===")
    print(f"Bucket destino: {BUCKET_NAME}")
    print(f"Objeto destino: {object_key}")

    # 1. Descargar dataset desde Datos Abiertos
    data = download_covid_csv()

    # 2. Subir archivo descargado a S3
    upload_to_s3(data, BUCKET_NAME, object_key)

    print("Proceso de ingestión finalizado correctamente.")


if __name__ == "__main__":
    main()
