"""Diagnostic script to capture StylesheetParseError details."""

import sys
import traceback
import logging

# Setup logging to capture all errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('diagnostic.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run ariatuc with enhanced error logging."""
    logger.info("Starting ariatuc with diagnostic logging...")

    try:
        from ariatuc.ui.app import AriatucApp

        logger.info("AriatucApp imported successfully")

        app = AriatucApp()
        logger.info("AriatucApp instantiated successfully")

        logger.info("Starting app.run()...")
        app.run()

    except Exception as e:
        logger.error(f"Fatal error: {type(e).__name__}: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

        # Check if it's a stylesheet error
        if "Stylesheet" in str(type(e)):
            logger.error("This is a Stylesheet-related error!")
            logger.error(f"Error details: {e}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error attributes: {e.__dict__}")

        sys.exit(1)

if __name__ == "__main__":
    main()
