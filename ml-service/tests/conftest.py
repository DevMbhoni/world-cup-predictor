from pathlib import Path
import sys


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]

sys.path.insert(0, str(PROJECT_ROOT))