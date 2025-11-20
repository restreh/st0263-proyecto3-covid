#!/usr/env/bin bash

VENV='venv'

echo "activating venv: $VENV"
source "$VENV/bin/activate"

BUCKET='jacostaa1datalake'

# Ingestion.
python3 scripts/download_covid_to_s3.py
python3 scripts/upload_rds_csv_to_s3.py

# Upload steps.
aws s3 cp scripts/*.py s3://$BUCKET/scripts/

# Create EMR cluster.
python3 scripts/create_emr_plus_steps.py
