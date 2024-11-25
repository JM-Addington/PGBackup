import os
import subprocess
import logging
from datetime import datetime

print("Welcome to the entrypoint script!")

logger = logging.getLogger(__name__)

PG_VERSION = os.getenv("PG_VERSION", "16")

try:
    subprocess.run(["apt", "install", "-y", f"postgresql-client-{PG_VERSION}"], check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Failed to install PostgreSQL client: {e}")
    exit(1)
except Exception as e:
    logger.error(f"An unexpected error occurred during PostgreSQL client installation: {e}")
    exit(1)

try:
    cron_schedule = os.getenv("CRON_SCHEDULE")
    post_backup_script = os.getenv("POSTBACKUPSCRIPT")
    
    # Set backup name
    friendly_name = os.getenv("FRIENDLY_NAME", os.getenv("POSTGRES_DB"))
    date_string = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_dir = os.getenv("OUTPUT_DIR", "/backup")
    output_path = f"/{output_dir}/{friendly_name}_{date_string}"
    
    enable_initial_backup = os.getenv("ENABLE_INITIAL_BACKUP", "false").lower() == "true"
    backup_command = ["python3", "/app/backup.py"]
    backup_command.extend(["--host", os.getenv("POSTGRES_HOST")])
    backup_command.extend(["--port", os.getenv("POSTGRES_PORT")])
    backup_command.extend(["--db", os.getenv("POSTGRES_DB")])
    backup_command.extend(["--user", os.getenv("POSTGRES_USER")])
    backup_command.extend(["--output", output_path])
    
    # Set password if provided by exporting POSTGRES_PASSWORD to PGPASSWORD
    if os.getenv("POSTGRES_PASSWORD"):
        os.environ["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD")

    if post_backup_script:
        backup_command.extend(["--post-backup-script", post_backup_script])
        
    if os.getenv("ENABLE_GPG", "false").lower() == "true":
        backup_command.append("--encrypt")
        
    # Set UID and GID if provided
    if os.getenv("UID"):
        backup_command.extend(["--uid", os.getenv("UID")])
    if os.getenv("GID"):
        backup_command.extend(["--gid", os.getenv("GID")])
        
    # Set GPG key if provided
    if os.getenv("KEY"):
        with open("/app/key", "w") as key_file:
            key_file.write(os.getenv("KEY"))
        os.chmod("/app/key", 0o600)

    # Set up cron job if CRON_SCHEDULE is set and start cron service
    if cron_schedule:
        try:
            cron_job = f"{cron_schedule} {' '.join(backup_command)} >> /var/log/cron.log 2>&1"
            with open("/etc/cron.d/backup-cron", "w") as cron_file:
                cron_file.write(cron_job + "\n")
            os.chmod("/etc/cron.d/backup-cron", 0o644)
            subprocess.run(["crontab", "/etc/cron.d/backup-cron"], check=True)
            open("/var/log/cron.log", "a").close()
            subprocess.run(["cron"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set up cron job or start cron service: {e}")
            exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred while setting up cron job: {e}")
            exit(1)
    
    # Run initial backup if ENABLE_INITIAL_BACKUP is set    
    if enable_initial_backup:
        logger.info("ENABLE_INITIAL_BACKUP is true. Running initial backup...")
        try:
            subprocess.run(backup_command, check=True)
            logger.info("Initial backup complete.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run initial backup: {e}")
            exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred during initial backup: {e}")
            exit(1)
        
    # If CRON_SCHEDULE is set, tail the cron log to keep the container running
    if cron_schedule:
        subprocess.run(["tail", "-f", "/var/log/cron.log"], check=True)

    else:
        logger.info("No CRON_SCHEDULE set. Running one-time backup...")
        subprocess.run(backup_command, check=True)
        logger.info("Backup complete. Exiting.")
except subprocess.CalledProcessError as e:
    logger.error(f"Failed to run backup or set up cron job: {e}")
    exit(1)
except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")
    exit(1)