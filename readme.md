# Overview
This project creates a Docker image that automatically backs up a PostgreSQL database to a mounted volume.

## Why?
Because I regularly need to back up databases where I already have all of the credentials stored in environment variables. Copying and pasting the values is redundant and error-prone. And backups were just one
more place to rotate crednetials.

I was also tired of fighting dbeaver to have the _exact_ correct pg_dump version installed on my machine.

This way, I can just set up a new service in my docker-compose file and be done with it, either locally during development or in production. The same secrets are used for the production database and the backup, and the
same docker-compose file can be moved across hosts with minimal changes.

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
UID=1000
GID=1000
ENABLE_GPG=true
KEY="
pgpkey
...
"
POSTBACKUPSCRIPT="/scripts/post-backup.sh"
```

For example, if you back up both a development and production database, each would have their
own env file.

`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are required. These are the credentials for the database you want to back up.

`PG_VERSION` is optional. If set, the backup will use the specified version of pg_dump. If not set, the backup will default to 16.

`CRON_SCHEDULE` is optional. If set, the backup will run on the schedule specified. If not set, the backup will run once when the container starts.

`FRIENDLY_NAME` is optional. If set, it will be added to the backup filename. 

`ENABLE_INITIAL_BACKUP` is optional. If set to `true`, a backup will run as soon as the container starts, not just on the schedule. _If `CRON_SCHEDULE` is not set, this will be ignored and the backup will run once when the container starts._

`UID` and `GID` are optional. If set, the backup will be owned by the specified user and group. Useful if you are mounting a volume that is owned by a different user. (i.e., with docker-compose, the container is owned by root, but you want to be able to access it from your user account.)

`ENABLE_GPG` is optional. If set to `true`, the backup will be encrypted with the PGP key. **When encryption is enabled no plaintext backup will
ever touch the disk.** The backup is piped to gzip, then to gpg, then to the mounted volume.

PGPKey needs to be an actual, public, PGP key. Everything will be encrypted with this key.

`POSTBACKUPSCRIPT` is optional. If set, the script will be run after the backup completes __successfully__. The first and only argument to the script will be the full path to the backup file. A sample script is included in the `scripts` directory.
- You can add your own scripts to the `scripts` directory and mount them to the container at `/scripts` to use them.

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
## Real Life Example
Here is a docker compose file that I use to run a production service. It uses
PGBackup for backup and remote_syslog2-docker for logging pgbackup (the production service) has
its own logging built in.
```yaml
services:
  AMS-Worker:
    image: myregistry.io/image:latest
    build: .
    env_file: .env.production
    restart: always

    networks:
        - internal

       watchtower:
         image: containrrr/watchtower
         volumes:
           - /var/run/docker.sock:/var/run/docker.sock
         command: --interval 3600

  backup:
    image: ghcr.io/jm-addington/pgbackup:latest
    env_file: .env.production
    restart: always
    environment:
      CRON_SCHEDULE: "0 20 * * *"
      PG_VERSION: 15
      ENABLE_GPG: true
      ENABLE_INITIAL_BACKUP: true
      POSTBACKUPSCRIPT: "/scripts/azcopy.sh"
      AZCOPY: "************"
      OUTPUT_DIR: /backups
      KEY: |
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        ...
        -----END PGP PUBLIC KEY BLOCK-----
    volumes:
        volumes:
      - /var/ams_backups:/backups/
      - ./logs/:/var/log/

  logging:
    image: ghcr.io/jmaddington/remote_syslog2-docker:latest
    command: ["/usr/local/bin/remote_syslog2", "-D", "--configfile", "/etc/rsyslog.yml"]

    volumes:
      - ./rsyslog.yml:/etc/rsyslog.yml
      - ./logs:/var/log/

    restart: always

networks:
  internal:
```