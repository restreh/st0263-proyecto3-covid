import os

import requests
import boto3

# CSV endpoint for COVID-19 cases in Colombia.
ROWS_LIMIT = os.getenv("ROWS_LIMIT", 5_000_000)
DATASET_URL = f"https://www.datos.gov.co/resource/gt2j-8ykr.csv?$limit={ROWS_LIMIT}"

# Prefijo dentro de la zona raw del bucket
RAW_PREFIX = "raw/covid"

# Nombre del bucket S3
# Usa la variable de entorno COVID_BUCKET_NAME si existe,
# de lo contrario usa el bucket por defecto del proyecto.
BUCKET_NAME = os.getenv("COVID_BUCKET_NAME", "st0263-proyecto3-covid19")

DATA_FILENAME = os.getenv("DATA_FILENAME", "casos_covid.csv")

OBJECT_KEY = f"{RAW_PREFIX}/{DATA_FILENAME}"


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
    print(f"bucket: {BUCKET_NAME}")
    print(f"filename: {DATA_FILENAME}")
    print(f"object key: {OBJECT_KEY}")

    data = download_covid_csv()
    upload_to_s3(data, BUCKET_NAME, OBJECT_KEY)

    print("ingest: done")


if __name__ == "__main__":
    main()
