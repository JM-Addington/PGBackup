#!/bin/bash

date=$(date +%Y-%m-%d_%H-%M-%S)

export PGPASSWORD=$POSTGRES_PASSWORD

# Set output directory and filename
OUTPUT_DIR=$OUTPUT_DIR

# If FRIENDLY_NAME is set use it, otherwise use POSTGRES_DB
if [ -z "$FRIENDLY_NAME" ]; then
    FRIENDLY_NAME=$POSTGRES_DB
else
    FRIENDLY_NAME=$FRIENDLY_NAME
fi

OUTPUT_NAME=$FRIENDLY_NAME-backup-$date.sql.gz

echo "Starting backup process..."
echo "HOST: $POSTGRES_HOST"
echo "FRIENDLY_NAME: $FRIENDLY_NAME"
echo "Output directory: $OUTPUT_DIR"
echo "Output name: $OUTPUT_NAME"

if [ "$ENABLE_GPG" = "true" ]; then
    # Remove existing key file and recreate it
    rm -f key
    printf "%s" "$KEY" > key
    chmod 600 key

    pg_dump --verbose -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT | \
        pv | \
        pigz -7 | \
        gpg --encrypt --recipient-file ./key \
        > "$OUTPUT_DIR/${OUTPUT_NAME}.gpg"

    echo "Backup complete with GPG encryption!"
else
    pg_dump --verbose -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT | \
        pigz -7 \
        > "$OUTPUT_DIR/$OUTPUT_NAME"

    echo "Backup complete without encryption!"
fi