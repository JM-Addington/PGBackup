#!/bin/bash

if [ -z "$PG_VERSION" ]; then
    PG_VERSION=16
fi

# Install the specified PG version
apt install -y "postgresql-client-$PG_VERSION"

# Run backup on initial launch if ENABLE_INITIAL_BACKUP is set to true
if [ "$ENABLE_INITIAL_BACKUP" = "true" ]; then
    /app/backup.sh
fi

if [ -n "$CRON_SCHEDULE" ]; then
    # Create cron schedule from environment variable CRON_SCHEDULE
    echo "$CRON_SCHEDULE /app/backup.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/backup-cron

    # Apply proper permissions
    chmod 0644 /etc/cron.d/backup-cron

    # Register cron job
    crontab /etc/cron.d/backup-cron

    # Create log file
    touch /var/log/cron.log

    # Start cron in the background
    cron

    # Keep the container running
    tail -f /var/log/cron.log
else
    echo "No CRON_SCHEDULE set. Running one-time backup..."
    /app/backup.sh
    echo "Backup complete. Exiting."
fi