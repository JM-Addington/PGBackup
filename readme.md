# Overview
This is a super simple project: it creates a docker image that will automatically
back up a postgres database to a mounted volume.

## Why?
Because I regularly need to back up databases where I already have all of the credentials stored in environment variables. Copying and pasting the values is redundant and error-prone. 

I was also tired of fighting dbeaver to have the _exact_ correct pg_dump version installed on my machine.

This way, I can just set up a new service in my docker-compose file and be done with it, either locally during development or in production.

# Usage
## Environment Variables
Create and edit a `.env` file in the root of this project. You will need one for each
backup configuration you want to run. The following variables MUST be set:
```bash
POSTGRES_HOST=pgbackup-dev-db
POSTGRES_PORT=5432
POSTGRES_DB=testdb
POSTGRES_USER=pgbackup
POSTGRES_PASSWORD=pgbackup
PG_VERSION=15
CRON_SCHEDULE="0 2 * * *"
OUTPUT_DIR="/backup"
OUTPUT_NAME="${POSTGRES_DB}-backup-${date}.sql.gz.gpg"
FRIENDLY_NAME=devdatabase
ENABLE_INITIAL_BACKUP=true
ENABLE_GPG=true
KEY="
pgpkey
...
"
```

For example, if you back up both a development and production database, each would have their
own env file.

`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are required. These are the credentials for the database you want to back up.

`PG_VERSION` is optional. If set, the backup will use the specified version of pg_dump. If not set, the backup will default to 16.

`CRON_SCHEDULE` is optional. If set, the backup will run on the schedule specified. If not set, the backup will run once when the container starts.

`FRIENDLY_NAME` is optional. If set, it will be added to the backup filename. 

`ENABLE_INITIAL_BACKUP` is optional. If set to `true`, a backup will run as soon as the container starts, not just on the schedule. _If `CRON_SCHEDULE` is not set, this will be ignored and the backup will run once when the container starts._

`ENABLE_GPG` is optional. If set to `true`, the backup will be encrypted with the PGP key. **When encryption is enabled no plaintext backup will
ever touch the disk.** The backup is piped to gzip, then to gpg, then to the mounted volume.

PGPKey needs to be an actual, public, PGP key. Everything will be encrypted with this key.

## Docker Compose
Edit your docker-compose file to create a service for each database backup configuration you
want to run. For example:
```yaml
services:
  pgbackup-production:
    image: pgbackup/prod
    volumes:
    - ./backup:/backup
  
    env_file:
      - .env.production

  pgbackup-dev:
    image: pgbackup/prod
    volumes:
    - ./backup:/backup

    env_file:
      - .env.production
```
`volumes` should be a single bind mount that points to the local directory OUTSIDE of the container
where you want to store your backups.

## Using with existing env files
If you already have a `.env` file for your project, you can use it with this project. Just add the env file to the compose file and then set the rest of the environment variables in your compose file. For example:
```yaml
services:

  # Actual production service
  my-production-service:
    image: my-production-service
    env_file:
      - .env.production

  # Add a backup service for the production database
  pgbackup-production:
    image: pgbackup/prod
    volumes:
    - ./backup:/backup
  
    env_file:
      - .env.production
    environment:
      - CRON_SCHEDULE="0 2 * * *"
      - FRIENDLY_NAME=production
      - ENABLE_INITIAL_BACKUP=true
      - ENABLE_GPG=true
      - KEY="
        pgpkey
        ...
        "
```
