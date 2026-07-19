"""Run the badge simulator headless and screenshot after N frames.

The sim's own --screenshot flag fires 5 frames in, which only ever
captures the OS boot splash; this driver raises the delay so the app
itself is on screen.  The sim saves to ./flow3r.png (in the sim
directory) and exits.  Run via `make sim-shot`, or directly:

    cd <badge-2024-software>/sim && python tools/sim_shot.py 400 hexling.HexlingApp
"""

import os
import sys

frames = int(sys.argv[1])
target = sys.argv[2]

sys.path.insert(0, os.getcwd())
sys.argv = ["run.py", "--screenshot", target]

import run  # noqa: E402  (module-level side effects set up the sim paths)

import _sim  # noqa: E402

_sim.SCREENSHOT_DELAY = frames

run.sim_main()
