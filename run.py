import sys
import os

# Ensure the src directory is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main

if __name__ == "__main__":
    main()
