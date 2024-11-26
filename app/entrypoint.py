import os
import subprocess
import logging
import argparse
import time 

print("Welcome to the entrypoint script!")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()

# Ensure the log directory exists
log_dir = os.path.dirname('/var/log/pgbackup.log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
file_handler = logging.FileHandler('/var/log/pgbackup.log')

# Create formatters and add them to handlers
formatter = logging.Formatter('[PGBACKUP] %(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logger.info("The date of this host is: %s", subprocess.run(["date"], stdout=subprocess.PIPE).stdout.decode().strip())

PG_VERSION = os.getenv("PG_VERSION", "16")

parser = argparse.ArgumentParser(description="Entrypoint script and cron job target")
parser.add_argument("--cron", required=False, type=bool, default=False, help="Run the cron job")
args = parser.parse_args()

if args.cron:
    logger.info("Running in cron mode.")

# Housekeeping if running for the first time
if args.cron == False:
    # If /scripts exists chmod +xr-w all files in it
    if os.path.exists("/scripts"):
        for file in os.listdir("/scripts"):
            os.chmod(f"/scripts/{file}", 0o555)

    try:
        logger.info("Installing PostgreSQL client...")
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
    output_dir = os.getenv("OUTPUT_DIR", "/backup")
    output_path = f"/{output_dir}/{friendly_name}"
    
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
    
    if args.cron == True:
        logger.info("Running the cron job backup.")
        try:
            subprocess.run(backup_command, check=True)
            logger.info("Cron backup complete.")
            exit(0)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run cron backup: {e}")
            exit(1)
        except Exception as e:
            logger.error(f"An unexpected error occurred during cron backup: {e}")
            exit(1)
    
    # Set up cron job if CRON_SCHEDULE is set and start cron service
    if cron_schedule:
        logger.info(f"Setting up cron job with schedule: {cron_schedule}")
        try:
            cron_job = f"{cron_schedule} touch /app/run"
            with open("/etc/cron.d/backup-cron", "w") as cron_file:
                cron_file.write(cron_job + "\n")
            os.chmod("/etc/cron.d/backup-cron", 0o644)
            subprocess.run(["crontab", "/etc/cron.d/backup-cron"], check=True)
            open("/var/log/cron.log", "a").close()
            subprocess.run(["cron"])
            logger.info("Cron job set up and cron service started.")
            
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
        
    # If CRON_SCHEDULE is set watch for the /app/run file and run the backup
    # It is set up this way because cron can't access the environment variables
    if cron_schedule:
        logger.info("Watching for /app/run file...")
        while True:  
            # Check to see if /app/run exists
            if os.path.exists("/app/run"):
                os.remove("/app/run")
                try:
                    subprocess.run(backup_command, check=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to run backup: {e}")
                    exit(1)
            else:
                logger.debug("No /app/run file found.")
                time.sleep(60)
                
    elif not enable_initial_backup:
        logger.info("No CRON_SCHEDULE set. Running one-time backup...")
        subprocess.run(backup_command, check=True)
        logger.info("Backup complete. Exiting.")
    
except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")
    exit(1)