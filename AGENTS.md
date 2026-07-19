# AGENTS.md — context that isn't discoverable from the code

Read the README first for controls, layout and commands. This file is
for the *why* and for facts about the environment, hardware and
firmware that you can't learn by reading this repo.

## Purpose and design intent

Hexling is a robot pet for the EMF Camp Tildagon badge (2026
"Spaceagon" frontboard) — a Tamagotchi with a body. Needs decay, moods
emerge; you feed, stroke and play. With a TeamRobotmad HexDrive
hexpansion fitted, moods are expressed physically (wiggle, look
around, shuffle). It is currently a **skeleton**: the structure and
plumbing are real and verified in the simulator, the behaviours are
deliberately minimal placeholders meant to be grown.

Intent that the code doesn't state:

- Moves are *expressions*, not navigation. The pet reacts; it does not
  drive around a room. Keep new moves short and character-driven.
- Needs decay demo-fast (minutes, see rates in `pet.py`) so the pet
  visibly changes during a hall demo. Real-pet timescales would become
  a setting later, not a retune of the constants.
- The badge is battery-powered and the HexDrive boost converter is
  hungry: the body powers up only when a move needs it, and
  spontaneous moves are rate-limited (`MOVE_COOLDOWN_MS`) partly for
  battery reasons. Preserve that behaviour.
- The motor/servo slew ramping in `hexdrive.py` is a hardware-safety
  measure, not a nicety: stepping the PWM duty browns out the badge
  (TeamRobotmad's template ramps for the same reason). Do not
  "simplify" it away.

## Project conventions (per Dave)

- **Vanilla Tildagon.** The official docs and example apps are the
  primary reference; take improvements from the third-party checkouts
  below. Do not import conventions from Dave's other personal badge
  projects.
- BadgeBot is the reference implementation for anything HexDrive.

## Local environment (this machine)

Everything is already checked out — never re-clone these:

- `~/projects/tildagon/official/badge-2024-software` — firmware +
  simulator (`sim/`). The Makefile's `SIM_DIR` defaults to this path.
- `~/projects/tildagon/official/badge-2024-documentation/docs/tildagon-apps/`
  — the docs, readable locally (`development.md`, `publish.md`,
  `reference/spaceagon.md`, `reference/ctx.md`).
- `~/projects/tildagon/thirdparty/` — `BadgeBot` (mature HexDrive app:
  hexpansion_mgr.py, motor_controller.py, sim-backed tests, typings/),
  `HexDriveUseTemplate` (minimal HexDrive app this skeleton drew on),
  `tildagon-avatar`, `tildenstein`.
- `.venv-sim/` here (create with `make venv`, needs uv; Python 3.10 to
  match the sim's requirements) holds sim deps + mpremote + pytest.

## Invariants to preserve

- `pet.py`, `moves.py`, `face.py`, `hexdrive.py` must import under
  plain CPython: no top-level badge imports (hardware imports live
  inside functions). This is what lets `make test` run with no
  simulator. `app.py` is the only badge-bound module.
- Moods are plain strings owned by `pet.py`; `face.py` keys its
  palette on the same literals instead of importing them. Deliberate:
  tests import these files as top-level modules (no package context),
  while the badge imports them as the `hexling` package — so leaf
  modules must not import each other. Only `app.py` uses relative
  imports.
- The `try: import system.scheduler` guard at the top of `app.py` is
  load-bearing for `make sim`: the sim's override_app imports this
  module before the firmware, and the firmware's eventbus<->scheduler
  import cycle only resolves when entered scheduler-first.
- `pet.tick()` is called from `background_update()` (which runs in
  fore- AND background, every ~50 ms) — never also tick it from
  `update()`, or the pet lives at double speed while focused.
- New runtime `.py` files must be added to `APP_FILES` in the Makefile
  (deploy copies only that list). New dev-only files must be added to
  `.gitattributes` as export-ignore (the app store ships everything
  that isn't ignored). `metadata.json` (sideload/launcher) and
  `tildagon.toml` (app store) must stay in sync on name/class.

## Simulator facts

- `make sim` symlinks this repo into `<SIM_DIR>/sim/apps/hexling` and
  runs `run.py hexling.HexlingApp`. Keyboard a–f = badge buttons.
- The sim boots as a **2024 frontboard** ("No eeprom detected,
  defaulting to 2024"): joystick, touch-strip and proximity events
  never fire there, even though a `frontboard2026` fake exists. Those
  input paths can only be exercised on hardware.
- No hexpansion EEPROMs exist in the sim, so `find_hexdrive()` always
  returns None — the "no HexDrive" path is the only body path the sim
  can test.
- Screenshots: `make sim-shot` (headless via SDL dummy drivers). The
  sim's native `--screenshot` fires 5 frames in and only ever captures
  the boot splash; `tools/sim_shot.py` raises `_sim.SCREENSHOT_DELAY`
  (~400 frames clears the splash). The sim exits after saving.
- `update(delta)`/`draw(ctx)` run every ~50 ms; `delta` is in
  milliseconds.

## Hardware facts (from docs/BadgeBot — not verifiable in the sim)

- HexDrive variants by hexpansion PID (VID 0xCAFE): 0xCBCA = 2 motor,
  0xCBCB = 2 motor + 4 servo, 0xCBCC = 4 servo, 0xCBCD = 1 motor +
  2 servo.
- Control goes through the HexDrive's EEPROM app, found in
  `scheduler.apps` (class name `HexDriveApp`, matching `config.port`).
  EEPROM detection needs badge firmware >= 1.8.
- EEPROM app surface used here: `get_status()`, `set_power(bool)`,
  `set_freq(hz)`, `set_motors(tuple_of_duty)`,
  `set_servoposition(i, us)`, and `set_servoposition()` with no args =
  all servos off. Servo positions are microseconds about the 1500 us
  centre, ±1000.
- **Nothing hardware-facing has been tried on a real badge or HexDrive
  yet**: motor polarity vs. the move scripts, servo ranges, current
  draw are all unverified. See the README bring-up checklist.
- The display is a round 240 px circle, coords -120..120 with (0,0) at
  centre: text near the bottom clips against the curve (keep status
  messages short — see `face.draw_status`).
- The badge runs MicroPython: no CPython-only stdlib in runtime
  modules, and keep memory use modest. Tests run under CPython, so
  every runtime module is effectively dual-target.

## Quirks worth knowing

- HexDriveUseTemplate's LICENSE file contains LGPL-2.1 text although
  its tildagon.toml declares LGPL-3.0-only; hexling ships the real
  LGPL-3.0 text.
- `tildagon.toml` `version` must be a **string**, and publishing needs
  the GitHub repo topic `tildagon-app` plus a release per version.
- The GitHub repo is `davesnowdon/hexling`; app-store publication
  still needs the `tildagon-app` repo topic and a tagged release.
- This project is tracked in lithos as `project:hexling`
  (`projects/hexling/hexling-project-context.md`), with a `related_to`
  edge to the sibling badge app `project:delvagon`.
