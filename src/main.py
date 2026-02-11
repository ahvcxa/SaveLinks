import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.repository import LinkRepository
from src.service.link_service import LinkService
from src.ui.cli import CLI
from src.core.logger import logger

def main():
    try:
        # Initialize components
        repo = LinkRepository()
        service = LinkService(repo)
        app = CLI(service)

        # Start the application
        app.start()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        print("A fatal error occurred. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
