import sys
from pathlib import Path

import_path = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(import_path))

import revoko
import revoko.daemon as daemon
