# Load env
import sys
from dotenv import load_dotenv
if "--debug" in sys.argv:
    load_dotenv(".env.debug")
else:
    load_dotenv(".env")

# Actual main
from src.logger import setup_logging
from src.overlay import start_overlay

def main():
    setup_logging()
    start_overlay()

if __name__ == "__main__":
    main()
