#!/bin/bash

date=`date +%Y-%m-%d_%H-%M-%S`

export PGPASSWORD=$POSTGRES_PASSWORD
rm key

printf "$KEY" > key
file="$date-$FRIENDLY_NAME-$POSTGRES_DB-backup.sql.gz.gpg"

#pg_dump "dbname=$POSTGRES_DB user=$POSTGRES_USER host=$POSTGRES_HOST port=$POSTGRES_PORT sslmode=require"

echo "Starting backup process..."
echo "$FRIENDLY_NAME"

pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -p $POSTGRES_PORT | \
    pv | \
    pigz -9 | \
    gpg --encrypt --recipient-file ./key \
    > /backup/$file

echo "Backup complete!"