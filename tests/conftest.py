"""Make the app's modules importable headless.

pet.py, moves.py, face.py and hexdrive.py deliberately avoid top-level
badge imports, so plain CPython + pytest is enough - no simulator or
hardware needed.  (app.py is badge-bound and is not imported here.)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
