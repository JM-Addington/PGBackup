import subprocess
import argparse
import logging
import os
from datetime import datetime

stderr_log_file = open('/var/log/pgbackup.log', 'a')

logger = logging.getLogger("PGBackup")
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()

# Ensure the log directory exists
log_dir = os.path.dirname('/var/log/pgbackup.log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
file_handler = logging.FileHandler('/var/log/pgbackup.log')

# Create formatters and add them to handlers
formatter = logging.Formatter('[PGBACKUP] %(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def main():
    parser = argparse.ArgumentParser(description="Backup script with optional GPG encryption and post-backup script.")
    parser.add_argument("--host", required=True, help="Database host")
    parser.add_argument("--user", required=True, help="Database user")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--port", required=True, help="Database port")
    parser.add_argument("--output", required=True, help="Output path for the backup file")
    parser.add_argument("--encrypt", action="store_true", help="Enable GPG encryption")
    parser.add_argument("--post-backup-script", help="Path to the post-backup script")
    parser.add_argument("--uid", type=int, help="UID for the backup file")
    parser.add_argument("--gid", type=int, help="GID for the backup file")
    args = parser.parse_args()
    
    # Get the current datetime and format it
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    
    # Prefix the filename with the current date by splitting the output path and inserting the current datetime
    split_path = args.output.split("/")
    split_path[-1] = f"{current_datetime}-{split_path[-1]}"
    output_path = "/".join(split_path)
    
    logger.info(f"Starting backup for database {args.db} on host {args.host} to {output_path}...")

    try:
        if args.encrypt:
            
            # Check that the key file exists
            if not os.path.exists("key"):
                raise FileNotFoundError("GPG key file not found. Please mount the key file to /app/key.")
            
            pg_dump_cmd = [
                "pg_dump", "--verbose", "-h", args.host, "-U", args.user, "-d", args.db, "-p", args.port
            ]
            pigz_cmd = ["pigz", "-7"]
            gpg_cmd = ["gpg", "--encrypt", "--recipient-file", "key"]

            with subprocess.Popen(pg_dump_cmd, stdout=subprocess.PIPE, stderr=stderr_log_file) as pg_dump_proc:
                with subprocess.Popen(pigz_cmd, stdin=pg_dump_proc.stdout, stdout=subprocess.PIPE, stderr=stderr_log_file) as pigz_proc:
                    with open(output_path + ".sql.gz.gpg", "wb") as output_file:
                        subprocess.run(gpg_cmd, stdin=pigz_proc.stdout, stdout=output_file,  stderr=stderr_log_file, check=True)

            logger.info("Backup complete with GPG encryption!")
            backup_file = output_path + ".sql.gz.gpg"
        else:
            pg_dump_cmd = [
                "pg_dump", "--verbose", "-h", args.host, "-U", args.user, "-d", args.db, "-p", args.port
            ]
            pigz_cmd = ["pigz", "-7"]

            with subprocess.Popen(pg_dump_cmd, stdout=subprocess.PIPE, stderr=stderr_log_file) as pg_dump_proc:
                with open(output_path, "wb") as output_file:
                    subprocess.run(pigz_cmd, stdin=pg_dump_proc.stdout, stdout=output_file, stderr=stderr_log_file, check=True)

            logger.info("Backup complete without encryption!")
            backup_file = output_path + ".sql.gz"

        if args.uid is not None and args.gid is not None:
            os.chown(backup_file, args.uid, args.gid)
            logger.info(f"Backup file ownership set to UID: {args.uid}, GID: {args.gid}")

        if args.post_backup_script:
            subprocess.run([args.post_backup_script, backup_file],stderr=stderr_log_file, stdout=stderr_log_file, check=True)
            logger.info("Post-backup script executed successfully!")

    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()