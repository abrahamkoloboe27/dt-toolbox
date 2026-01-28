"""Example of successful script execution with dt-toolbox monitoring."""

import logging
import time

from dt_toolbox import init_monitoring

# Initialize monitoring
logger = init_monitoring(
    app_name="example_success",
    owner="abklb27@gmail.com",
    recipients=["data-team@company.com"],
    tags=["example", "success"],
    notify_on_success=True,  # Enable success notifications for this example
)


def process_data():
    """Simulate data processing."""
    logger.info("Starting data processing...")

    for i in range(5):
        time.sleep(0.5)
        logger.info(f"Processing batch {i + 1}/5")

    logger.info("Data processing completed successfully")


def main():
    """Main function."""
    logger.info("Application started")

    # Simulate some work
    process_data()

    logger.info("Application finished successfully")


if __name__ == "__main__":
    main()
