"""Hexling - a robot pet for the Tildagon badge.

Badge glue only: lifecycle, input, screen and HexDrive wiring.  The
pet's behaviour lives in pet.py, scripted body moves in moves.py,
HexDrive access in hexdrive.py and drawing in face.py.
"""

# When run via the simulator's override_app (`make sim`) this module is
# imported before the firmware, and the eventbus<->scheduler import
# cycle only resolves when entered scheduler-first.
try:
    import system.scheduler  # noqa: F401
except ImportError:
    pass

import app

from events.input import BUTTON_TYPES, ButtonDownEvent, Buttons
from system.eventbus import eventbus
from system.hexpansion.events import (HexpansionInsertionEvent,
                                      HexpansionRemovalEvent)

from . import face
from .hexdrive import find_hexdrive
from .moves import MoveRunner
from .pet import Pet

# What each direction plays when you nudge the pet (joystick on the
# Spaceagon, A/B/D/E buttons on a 2024 frontboard).
_NUDGE_MOVES = {
    "UP": "shuffle",
    "DOWN": "look_around",
    "LEFT": "wiggle",
    "RIGHT": "wiggle",
}


class HexlingApp(app.App):
    def __init__(self):
        super().__init__()
        self.button_states = Buttons(self)
        self.pet = Pet()
        self.moves = MoveRunner()
        self.hexdrive = None
        self._scan_needed = True
        self._wall_ms = 0

        # Spaceagon touch strip / proximity sensors arrive as plain
        # ButtonDownEvents; matching by name means this is a harmless
        # no-op on a 2024 frontboard.
        eventbus.on(ButtonDownEvent, self._on_button_down, self)
        eventbus.on_async(HexpansionInsertionEvent, self._on_hexpansion_change, self)
        eventbus.on_async(HexpansionRemovalEvent, self._on_hexpansion_change, self)

    # ---- event handlers ----------------------------------------------

    async def _on_hexpansion_change(self, event):
        self._scan_needed = True

    def _on_button_down(self, event):
        name = event.button.name
        if name.startswith("TOUCH"):
            self.pet.stroke()  # stroking the touch strip pets the hexling
        elif name.endswith("PROX"):
            self.pet.wake()  # a hand waved nearby wakes it

    # ---- app lifecycle -----------------------------------------------

    def update(self, delta):
        if self._scan_needed:
            self._scan_needed = False
            self._rescan()

        buttons = self.button_states
        if buttons.get(BUTTON_TYPES["CANCEL"]):
            buttons.clear()
            self._stop_body()
            self.minimise()
            return
        if buttons.get(BUTTON_TYPES["CONFIRM"]):
            buttons.clear()
            self.pet.feed()
        else:
            for direction, move in _NUDGE_MOVES.items():
                if buttons.get(BUTTON_TYPES[direction]):
                    buttons.clear()
                    self.pet.play()
                    self.moves.start(move)
                    break

        self._wall_ms += delta
        if not self.moves.active:
            suggestion = self.pet.suggest_move()
            if suggestion:
                self.moves.start(suggestion)
        self._drive_body(delta)

    def background_update(self, delta):
        # Runs in fore- and background: the pet keeps living (and can
        # fall asleep, get hungry...) while the app is minimised.
        self.pet.tick(delta)

    def draw(self, ctx):
        face.draw(ctx, self.pet.mood, self._wall_ms)
        if self.hexdrive is None:
            face.draw_status(ctx, "no HexDrive")
        self.draw_overlays(ctx)

    # ---- body control ------------------------------------------------

    def _rescan(self):
        self._stop_body()
        self.hexdrive = find_hexdrive()

    def _drive_body(self, delta):
        step = self.moves.tick(delta)
        if self.hexdrive is None:
            return
        if step is None:
            self.hexdrive.set_targets(motors=(0.0, 0.0), servos=(0, 0, 0, 0))
        else:
            motors, servos = step
            self.hexdrive.set_targets(motors, servos)
            if not self.hexdrive.powered and not self.hexdrive.start():
                print("Hexling: HexDrive PWM resources unavailable")
                self.hexdrive = None
                return
        self.hexdrive.tick(delta)

    def _stop_body(self):
        self.moves.stop()
        if self.hexdrive is not None and self.hexdrive.powered:
            try:
                self.hexdrive.stop()
            except Exception:
                # The hexpansion may just have been unplugged mid-move.
                pass


__app_export__ = HexlingApp
