"""Example using the @monitor decorator."""

import logging
import time

from dt_toolbox import monitor


@monitor(
    owner="abklb27@gmail.com",
    recipients=["data-team@company.com"],
    tags=["example", "decorator"],
    notify_on_success=True,
)
def main():
    """Main function with monitoring."""
    logger = logging.getLogger()

    logger.info("Starting processing with decorator...")

    for i in range(3):
        time.sleep(0.5)
        logger.info(f"Step {i + 1}/3 completed")

    logger.info("All processing completed successfully")


if __name__ == "__main__":
    main()
