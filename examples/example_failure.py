"""Example of failed script execution with dt-toolbox monitoring."""

import logging
import time

from dt_toolbox import init_monitoring

# Initialize monitoring
logger = init_monitoring(
    app_name="example_failure",
    owner="abklb27@gmail.com",
    recipients=["data-team@company.com"],
    tags=["example", "failure"],
    notify_on_success=False,  # Only notify on failure
)


def process_data():
    """Simulate data processing with failure."""
    logger.info("Starting data processing...")

    for i in range(3):
        time.sleep(0.5)
        logger.info(f"Processing batch {i + 1}/5")

    # Simulate an error
    logger.error("Critical error encountered during processing")
    raise ValueError("Failed to process data: Invalid data format in batch 3")


def main():
    """Main function."""
    logger.info("Application started")

    # This will raise an exception
    process_data()

    # This line will not be reached
    logger.info("Application finished")


if __name__ == "__main__":
    main()
