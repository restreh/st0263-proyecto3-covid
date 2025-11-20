import os
import boto3

BUCKET_NAME = os.getenv("COVID_BUCKET_NAME", "st0263-proyecto3-covid19")

LOCAL_RDS_DIR = "data/rds"
RAW_RDS_PREFIX = "raw/rds"


def upload_file(local_path: str, bucket: str, key: str) -> None:
    print(f"Subiendo {local_path} a s3://{bucket}/{key} ...")
    s3 = boto3.client("s3")
    with open(local_path, "rb") as f:
        s3.put_object(Bucket=bucket, Key=key, Body=f)
    print("OK")


def main() -> None:
    print("=== Subida de CSV 'RDS' a S3 (zona raw/rds) ===")
    files = [
        "departamento_demografia.csv",
        "departamento_capacidad_hospitalaria.csv",
    ]

    for fname in files:
        local_path = os.path.join(LOCAL_RDS_DIR, fname)
        key = f"{RAW_RDS_PREFIX}/{fname}"
        if not os.path.isfile(local_path):
            print(f"[ADVERTENCIA] No existe el archivo local: {local_path}")
            continue
        upload_file(local_path, BUCKET_NAME, key)

    print("Proceso completado.")


if __name__ == "__main__":
    main()
