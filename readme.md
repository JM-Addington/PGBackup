# Overview
This is a super simple project: it creates a docker image that will automatically
back up a postgres database to a mounted volume.

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
FRIENDLY_NAME=devdatabase
KEY="
pgpkey
...
"
```

For example, if you back up both a development and production database, each would have their
own env file.

PGPKey needs to be an actual, public, PGP key. Everything will be encrypted with this key.

`FRIENDLY_NAME` is optional. If set, it will be added to the backup filename. 

## Docker Compose
Edit your docker-compose file to create a service for each database backup configuration you
want to run. For example:
```yaml
version: '3'

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