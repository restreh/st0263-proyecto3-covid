#!/usr/bin/env bash

# Run COVID-19 ETL pipeline: fetch data, upload to S3, process on EMR.

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# Constants
readonly VENV='venv'
readonly BUCKET='jacostaa1datalake'
readonly REQUIREMENTS='requirements/prod.txt'

# Set environment variable for scripts
export COVID_BUCKET_NAME="$BUCKET"

# Main execution
main() {
    echo "pipeline: starting"
    echo "config: bucket=$BUCKET, venv=$VENV"

    # Activate virtual environment
    if [[ ! -d "$VENV" ]]; then
        echo "error: venv not found at $VENV"
        exit 1
    fi

    echo "activating venv"
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"

    # Install dependencies
    echo "installing requirements from $REQUIREMENTS"
    pip install -q -r "$REQUIREMENTS"
    echo "install: done"

    # Step 1: Ingest raw data to S3
    echo "ingestion: starting"
    python3 scripts/download_covid_to_s3.py
    python3 scripts/upload_csv_to_rds.py
    python3 scripts/export_rds_to_s3.py
    echo "ingestion: done"

    # Step 2: Upload Spark scripts to S3
    echo "uploading scripts to s3://$BUCKET/scripts/"
    aws s3 cp scripts "s3://$BUCKET/scripts/" \
        --recursive \
        --exclude "*" \
        --include "*.py"
    echo "upload scripts: done"

    # Step 3: Create EMR cluster and run processing steps
    echo "emr: starting cluster and steps"
    python3 scripts/create_emr_plus_steps.py
    echo "emr: done"

    echo "pipeline: done"
}

# Run main function
main "$@"
