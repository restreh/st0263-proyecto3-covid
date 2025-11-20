import os
from pathlib import Path
from typing import List

import pandas as pd
import pymysql
import boto3

# Constants - RDS configuration
RDS_HOST = os.getenv("RDS_HOST")
RDS_PORT = int(os.getenv("RDS_PORT", "3306"))
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DATABASE = os.getenv("RDS_DATABASE", "datos_complementarios")

# Constants - S3 configuration
BUCKET_NAME = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
S3_PREFIX = "raw/rds"

# Constants - Export configuration
TABLES_TO_EXPORT = ["poblacion"]
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "csv")  # csv or parquet
LOCAL_EXPORT_DIR = Path(__file__).parent.parent / "data"


def validate_credentials() -> None:
    """
    Validate that required RDS credentials are set.

    Raises:
        ValueError: If any required credential is missing
    """
    missing = []
    if not RDS_HOST:
        missing.append("RDS_HOST")
    if not RDS_USER:
        missing.append("RDS_USER")
    if not RDS_PASSWORD:
        missing.append("RDS_PASSWORD")

    if missing:
        raise ValueError(f"missing required environment variables: {', '.join(missing)}")


def export_table_to_file(
    connection, table_name: str, output_dir: Path, file_format: str
) -> Path:
    """
    Export a MySQL table to a local file using pandas.

    Args:
        connection: PyMySQL connection object
        table_name: Name of table to export
        output_dir: Directory to save exported files
        file_format: Output format (csv or parquet)

    Returns:
        Path to exported file
    """
    print(f"exporting table: {table_name}")

    # Read table into DataFrame
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, connection)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to file based on format
    if file_format == "parquet":
        file_path = output_dir / f"{table_name}.parquet"
        df.to_parquet(file_path, index=False)
    else:  # default to csv
        file_path = output_dir / f"{table_name}.csv"
        df.to_csv(file_path, index=False)

    print(f"export: done ({file_path}, {len(df)} rows)")
    return file_path


def upload_to_s3(file_path: Path, bucket: str, s3_key: str) -> None:
    """
    Upload a local file to S3.

    Args:
        file_path: Local file path
        bucket: S3 bucket name
        s3_key: S3 object key
    """
    print(f"uploading to s3://{bucket}/{s3_key}")

    s3 = boto3.client("s3")
    s3.upload_file(str(file_path), bucket, s3_key)

    print("upload: done")


def export_tables(tables: List[str]) -> None:
    """
    Export multiple tables from RDS to local files and upload to S3.

    Args:
        tables: List of table names to export
    """
    print(f"connecting to mysql://{RDS_USER}@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}")

    try:
        connection = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DATABASE,
            charset="utf8mb4",
        )
        print("connection: established")

        for table_name in tables:
            # Export table to local file
            local_file = export_table_to_file(
                connection, table_name, LOCAL_EXPORT_DIR, OUTPUT_FORMAT
            )

            # Upload to S3
            s3_key = f"{S3_PREFIX}/{table_name}.{OUTPUT_FORMAT}"
            upload_to_s3(local_file, BUCKET_NAME, s3_key)

        print(f"rds export: done ({len(tables)} tables)")

    except pymysql.Error as e:
        print(f"error: mysql connection failed - {e}")
        print(f"error: check RDS security group allows inbound from your IP on port {RDS_PORT}")
        print("error: verify RDS instance has public accessibility enabled")
        raise

    finally:
        if connection:
            connection.close()
            print("connection: closed")


def main() -> None:
    """
    Export RDS MySQL tables to S3 raw zone.

    Steps:
    1. Validate RDS credentials from environment variables
    2. Connect to RDS MySQL instance
    3. Export each table to local file (CSV or Parquet)
    4. Upload files to S3 raw/rds/ prefix
    """
    print(f"config: host={RDS_HOST}, database={RDS_DATABASE}")
    print(f"config: bucket={BUCKET_NAME}, format={OUTPUT_FORMAT}")
    print(f"config: tables={TABLES_TO_EXPORT}")

    # Validate credentials
    validate_credentials()

    # Export tables
    export_tables(TABLES_TO_EXPORT)

    print("rds to s3: done")


if __name__ == "__main__":
    main()
