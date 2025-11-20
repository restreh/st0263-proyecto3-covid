import os
from pathlib import Path

import requests
import boto3

# Constants - Dataset configuration
ROWS_LIMIT = os.getenv("ROWS_LIMIT", 1_000_000)
DATASET_URL = f"https://www.datos.gov.co/resource/gt2j-8ykr.csv?$limit={ROWS_LIMIT}"

# Constants - Local paths
DATA_DIR = Path(__file__).parent.parent / "data"
LOCAL_FILENAME = os.getenv("DATA_FILENAME", "casos_covid.csv")
LOCAL_FILE_PATH = DATA_DIR / LOCAL_FILENAME

# Constants - S3 configuration
BUCKET_NAME = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
RAW_PREFIX = "raw/covid"
OBJECT_KEY = f"{RAW_PREFIX}/{LOCAL_FILENAME}"


def download_covid_csv(url: str, output_path: Path) -> None:
    """
    Download COVID-19 CSV dataset from Datos Abiertos Colombia API.

    Args:
        url: API endpoint URL
        output_path: Local file path where CSV will be saved
    """
    if output_path.exists():
        print(f"download: skipped (file exists at {output_path})")
        return

    print(f"downloading from {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    output_path.write_bytes(response.content)
    print(f"download: done ({output_path})")


def upload_to_s3(file_path: Path, bucket: str, key: str) -> None:
    """
    Upload a local file to an S3 bucket.

    Args:
        file_path: Path to local file
        bucket: S3 bucket name
        key: S3 object key
    """
    print(f"uploading to s3://{bucket}/{key}")
    s3 = boto3.client("s3")

    with open(file_path, "rb") as f:
        s3.put_object(Bucket=bucket, Key=key, Body=f)

    print("upload: done")


def main() -> None:
    """
    Download COVID-19 cases dataset and upload to S3 raw zone.

    Steps:
    1. Download CSV from API to local data directory (if not exists)
    2. Upload local file to S3 bucket
    """
    print(f"config: bucket={BUCKET_NAME}, local_file={LOCAL_FILE_PATH}")
    print(f"config: s3_key={OBJECT_KEY}, rows_limit={ROWS_LIMIT}")

    # Download CSV to local file (only if it doesn't exist)
    download_covid_csv(DATASET_URL, LOCAL_FILE_PATH)

    # Upload to S3
    upload_to_s3(LOCAL_FILE_PATH, BUCKET_NAME, OBJECT_KEY)

    print("datos abiertos process: done")


if __name__ == "__main__":
    main()
