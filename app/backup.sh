#!/bin/bash

date=`date +%Y-%m-%d_%H-%M-%S`

export PGPASSWORD=$POSTGRES_PASSWORD
rm key

printf "$KEY" > key
file="$date-$POSTGRES_DB-backup.sql.gz.gpg"

pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB | \
    pigz -9 | 
    gpg --encrypt --recipient-file ./key \
    > $file