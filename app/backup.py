import subprocess
import argparse
import logging
import os

logger = logging.getLogger(__name__)

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

    output_path = args.output

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

            with subprocess.Popen(pg_dump_cmd, stdout=subprocess.PIPE) as pg_dump_proc:
                with subprocess.Popen(pigz_cmd, stdin=pg_dump_proc.stdout, stdout=subprocess.PIPE) as pigz_proc:
                    with open(output_path + ".sql.gz.gpg", "wb") as output_file:
                        subprocess.run(gpg_cmd, stdin=pigz_proc.stdout, stdout=output_file, check=True)

            logger.info("Backup complete with GPG encryption!")
            backup_file = output_path + ".sql.gz.gpg"
        else:
            pg_dump_cmd = [
                "pg_dump", "--verbose", "-h", args.host, "-U", args.user, "-d", args.db, "-p", args.port
            ]
            pigz_cmd = ["pigz", "-7"]

            with subprocess.Popen(pg_dump_cmd, stdout=subprocess.PIPE) as pg_dump_proc:
                with open(output_path, "wb") as output_file:
                    subprocess.run(pigz_cmd, stdin=pg_dump_proc.stdout, stdout=output_file, check=True)

            logger.info("Backup complete without encryption!")
            backup_file = output_path + ".sql.gz"

        if args.uid is not None and args.gid is not None:
            os.chown(backup_file, args.uid, args.gid)
            logger.info(f"Backup file ownership set to UID: {args.uid}, GID: {args.gid}")

        if args.post_backup_script:
            subprocess.run([args.post_backup_script, backup_file], check=True)
            logger.info("Post-backup script executed successfully!")

    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()