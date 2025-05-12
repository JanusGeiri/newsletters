#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

# Set up logging directory
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

# Generate timestamp for log file
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = LOGS_DIR / f'automation_{timestamp}.log'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format."""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = datetime.now()
    return yesterday.strftime('%Y-%m-%d')


def run_command(command, description):
    """Run a shell command and log its output."""
    logger.info(f"Running {description}...")
    try:
        # Run the command and stream output in real-time
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())  # Print to terminal
                logger.info(f"[{description}] {output.strip()}")  # Log to file

        # Get any remaining output
        remaining_output, stderr = process.communicate()

        # Log any remaining output
        if remaining_output:
            print(remaining_output.strip())
            logger.info(f"[{description}] {remaining_output.strip()}")

        # Log any errors
        if stderr:
            print(stderr.strip(), file=sys.stderr)
            logger.error(f"[{description}] Error: {stderr.strip()}")

        # Check if the process was successful
        if process.returncode == 0:
            logger.info(f"{description} completed successfully")
            return True
        else:
            logger.error(
                f"{description} failed with return code {process.returncode}")
            return False

    except Exception as e:
        logger.error(f"Error running {description}: {str(e)}")
        return False


def main():
    """Main automation function."""
    logger.info("Starting newsletter automation process")

    # Step 1: Process unsubscribes
    unsub_command = [
        sys.executable,
        "process_unsubscribes.py"
    ]

    if not run_command(unsub_command, "processing unsubscribes"):
        logger.error("Processing unsubscribes failed. Stopping automation.")
        return
    logger.info("Unsubscribe processing completed successfully")

    # Get yesterday's date
    yesterday = get_yesterday_date()
    logger.info(f"Processing newsletter for date: {yesterday}")

    # Step 2: Generate the newsletter
    generate_command = [
        sys.executable,  # Use the same Python interpreter
        "main.py",
        "--mode", "full_pipeline",
        "--daily-morning",
        "--date", yesterday
    ]

    if not run_command(generate_command, "newsletter generation"):
        logger.error("Newsletter generation failed. Stopping automation.")
        return
    logger.info("Newsletter generation completed successfully")

    # Step 3: Update the index
    send_command = [
        sys.executable,
        "update_index.py"
    ]

    if not run_command(send_command, "updating index"):
        logger.error("Updating index failed.")
        return

    logger.info("Updating index completed successfully")

    # Step 4: Send the newsletter
    send_command = [
        sys.executable,
        "send_newsletter.py",
        "--date", yesterday,
    ]

    if not run_command(send_command, "newsletter sending"):
        logger.error("Newsletter sending failed.")
        return

    logger.info("Newsletter automation completed successfully")


if __name__ == "__main__":
    main()
