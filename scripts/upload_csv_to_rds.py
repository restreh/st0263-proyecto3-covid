import os
import csv
from pathlib import Path
from typing import List, Tuple

import pymysql

# Constants - RDS configuration
RDS_HOST = os.getenv("RDS_HOST")
RDS_PORT = int(os.getenv("RDS_PORT", "3306"))
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DATABASE = os.getenv("RDS_DATABASE", "datos_complementarios")

# Constants - Local paths
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_FILENAME = "rds_departamento_demografia.csv"
CSV_FILE_PATH = DATA_DIR / CSV_FILENAME

# Constants - Table configuration
TABLE_NAME = "poblacion"


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


def read_csv_data(file_path: Path) -> Tuple[List[str], List[Tuple]]:
    """
    Read CSV file and return headers and data rows.

    Args:
        file_path: Path to CSV file

    Returns:
        Tuple of (column_names, data_rows)
    """
    print(f"reading csv from {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        data = [tuple(row) for row in reader]

    print(f"read: {len(data)} rows, {len(headers)} columns")
    return headers, data


def create_database(connection) -> None:
    """
    Create database if it doesn't exist.

    Args:
        connection: PyMySQL connection object
    """
    print(f"creating database: {RDS_DATABASE}")

    with connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {RDS_DATABASE}")
        cursor.execute(f"USE {RDS_DATABASE}")

    connection.commit()
    print("create database: done")


def create_table(connection) -> None:
    """
    Create poblacion table if it doesn't exist.

    Args:
        connection: PyMySQL connection object
    """
    print(f"creating table: {TABLE_NAME}")

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        codigo_departamento VARCHAR(2) PRIMARY KEY,
        departamento VARCHAR(100) NOT NULL,
        poblacion INT NOT NULL
    )
    """

    with connection.cursor() as cursor:
        cursor.execute(create_table_sql)

    connection.commit()
    print("create table: done")


def insert_data(connection, headers: List[str], data: List[Tuple]) -> None:
    """
    Insert CSV data into the table using batch insert.

    Args:
        connection: PyMySQL connection object
        headers: Column names from CSV
        data: Data rows to insert
    """
    if not data:
        print("insert: skipped (no data)")
        return

    print(f"inserting {len(data)} rows into {TABLE_NAME}")

    # Build INSERT statement
    columns = ", ".join(headers)
    placeholders = ", ".join(["%s"] * len(headers))
    insert_sql = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"

    # Handle duplicate keys by updating existing records
    update_clause = ", ".join([f"{col}=VALUES({col})" for col in headers if col != headers[0]])
    insert_sql += f" ON DUPLICATE KEY UPDATE {update_clause}"

    with connection.cursor() as cursor:
        cursor.executemany(insert_sql, data)

    connection.commit()
    print(f"insert: done ({cursor.rowcount} rows affected)")


def main() -> None:
    """
    Upload CSV data to RDS MySQL database.

    Steps:
    1. Validate RDS credentials from environment variables
    2. Read CSV data from local file
    3. Connect to RDS MySQL instance
    4. Create database and table if they don't exist
    5. Insert data into table
    """
    print(f"config: host={RDS_HOST}, port={RDS_PORT}, database={RDS_DATABASE}")
    print(f"config: csv_file={CSV_FILE_PATH}")

    # Validate credentials
    validate_credentials()

    # Read CSV data
    headers, data = read_csv_data(CSV_FILE_PATH)

    # Connect to RDS
    print(f"connecting to mysql://{RDS_USER}@{RDS_HOST}:{RDS_PORT}")

    try:
        connection = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.Cursor,
        )
        print("connection: established")

        # Setup database and table
        create_database(connection)
        create_table(connection)

        # Insert data
        insert_data(connection, headers, data)

        print("rds upload: done")

    except pymysql.Error as e:
        print(f"error: {e}")
        raise

    finally:
        if connection:
            connection.close()
            print("connection: closed")


if __name__ == "__main__":
    main()
