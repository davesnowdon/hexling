"""Scripted body moves for the HexDrive.

A move is a tuple of steps; a step is (duration_ms, motors, servos):

* motors: (left, right) power fractions in -1.0..1.0, or None to leave
  the motor targets alone for this step.
* servos: up to 4 positions in microseconds relative to the 1500us
  centre (-1000..1000), or None to leave the servo targets alone.

Moves are written against the largest HexDrive (2 motors + 4 servos);
channels the fitted hardware doesn't have are ignored by the HexDrive
wrapper, so every move works on every variant.  Pure Python, no badge
imports.
"""

STOP_MOTORS = (0.0, 0.0)
CENTRE_SERVOS = (0, 0, 0, 0)

MOVES = {
    # A happy little shimmy on the spot.
    "wiggle": (
        (250, (0.4, -0.4), (200, -200, 200, -200)),
        (250, (-0.4, 0.4), (-200, 200, -200, 200)),
        (250, (0.4, -0.4), (200, -200, 200, -200)),
        (250, STOP_MOTORS, CENTRE_SERVOS),
    ),
    # Creep forward and back, like sniffing at something.
    "shuffle": (
        (300, (0.5, 0.5), None),
        (200, STOP_MOTORS, None),
        (300, (-0.5, -0.5), None),
        (200, STOP_MOTORS, None),
    ),
    # Slow head-turn each way (servo 1), motors untouched.
    "look_around": (
        (400, None, (400, 0, 0, 0)),
        (400, None, (-400, 0, 0, 0)),
        (300, None, CENTRE_SERVOS),
    ),
}


class MoveRunner:
    """Plays one move script at a time.

    Call tick(delta_ms) every frame: it returns the active step's
    (motors, servos) targets, or None when no move is playing.
    """

    def __init__(self):
        self._steps = None
        self._index = 0
        self._remaining_ms = 0

    @property
    def active(self):
        return self._steps is not None

    def start(self, name):
        """Start the named move, replacing any move in progress.
        Unknown names are ignored so pet.py can suggest freely."""
        steps = MOVES.get(name)
        if not steps:
            return
        self._steps = steps
        self._index = 0
        self._remaining_ms = steps[0][0]

    def stop(self):
        self._steps = None

    def tick(self, delta_ms):
        if self._steps is None:
            return None
        self._remaining_ms -= delta_ms
        # A slow frame may consume more than one step.
        while self._remaining_ms <= 0:
            self._index += 1
            if self._index >= len(self._steps):
                self._steps = None
                return None
            self._remaining_ms += self._steps[self._index][0]
        _, motors, servos = self._steps[self._index]
        return motors, servos
