"""Hexling's brain: needs, moods and behaviour.

Pure Python with no badge imports, so it can be developed and tested
headless with pytest (`make test`).  Time is fed in as millisecond
deltas by the app's update loop.
"""

import random

# Needs run 0.0 (critical) .. 1.0 (satisfied) and decay over time.
# Rates are per millisecond, tuned demo-fast so the pet visibly changes
# within a single play session rather than over days.
FOOD_DECAY_PER_MS = 1.0 / (5 * 60 * 1000)  # full -> starving in ~5 min
FUN_DECAY_PER_MS = 1.0 / (3 * 60 * 1000)   # entertained -> bored in ~3 min
REST_DECAY_PER_MS = 1.0 / (8 * 60 * 1000)  # awake cost: sleepy after ~8 min
REST_RECOVERY_PER_MS = 1.0 / (30 * 1000)   # asleep: fully rested in ~30 s

FEED_AMOUNT = 0.35
STROKE_FUN = 0.15
PLAY_FUN = 0.30
PLAY_REST_COST = 0.05

ASLEEP_BELOW = 0.15  # falls asleep when rest drops below this
WAKE_ABOVE = 0.90    # wakes naturally when rest recovers above this
HUNGRY_BELOW = 0.30
BORED_BELOW = 0.30
HAPPY_ABOVE = 0.75   # both food and fun above this = happy

# Moods, checked in priority order; face.py keys its palette on these
# same strings.
MOOD_ASLEEP = "asleep"
MOOD_HUNGRY = "hungry"
MOOD_BORED = "bored"
MOOD_HAPPY = "happy"
MOOD_CONTENT = "content"

# Minimum gap between spontaneous body moves, and the chance per
# elapsed cooldown that a move actually happens.
MOVE_COOLDOWN_MS = 6000
MOVE_CHANCE = 0.5

# What the body does in each mood (move names from moves.py).
_MOOD_MOVES = {
    MOOD_HAPPY: "wiggle",
    MOOD_BORED: "look_around",
    MOOD_HUNGRY: "shuffle",
}


def _clamp(value):
    return min(1.0, max(0.0, value))


class Pet:
    def __init__(self, rng=None):
        self._rng = rng if rng is not None else random.Random()
        self.food = 0.8
        self.fun = 0.8
        self.rest = 1.0
        self.asleep = False
        self._move_cooldown_ms = MOVE_COOLDOWN_MS

    @property
    def mood(self):
        if self.asleep:
            return MOOD_ASLEEP
        if self.food < HUNGRY_BELOW:
            return MOOD_HUNGRY
        if self.fun < BORED_BELOW:
            return MOOD_BORED
        if self.food > HAPPY_ABOVE and self.fun > HAPPY_ABOVE:
            return MOOD_HAPPY
        return MOOD_CONTENT

    def tick(self, delta_ms):
        """Advance needs by delta_ms milliseconds."""
        self.food = _clamp(self.food - FOOD_DECAY_PER_MS * delta_ms)
        if self.asleep:
            self.rest = _clamp(self.rest + REST_RECOVERY_PER_MS * delta_ms)
            if self.rest > WAKE_ABOVE:
                self.asleep = False
        else:
            self.fun = _clamp(self.fun - FUN_DECAY_PER_MS * delta_ms)
            self.rest = _clamp(self.rest - REST_DECAY_PER_MS * delta_ms)
            if self.rest < ASLEEP_BELOW:
                self.asleep = True
        if self._move_cooldown_ms > 0:
            self._move_cooldown_ms -= delta_ms

    # ---- interactions ------------------------------------------------

    def wake(self):
        if self.asleep:
            self.asleep = False

    def feed(self):
        self.wake()
        self.food = _clamp(self.food + FEED_AMOUNT)

    def stroke(self):
        self.wake()
        self.fun = _clamp(self.fun + STROKE_FUN)

    def play(self):
        self.wake()
        self.fun = _clamp(self.fun + PLAY_FUN)
        self.rest = _clamp(self.rest - PLAY_REST_COST)

    # ---- body --------------------------------------------------------

    def suggest_move(self):
        """A spontaneous move name for the body, or None.

        Rate-limited by a cooldown so the pet is animated but not
        frantic (and doesn't flatten the badge battery).
        """
        if self.asleep or self._move_cooldown_ms > 0:
            return None
        self._move_cooldown_ms = MOVE_COOLDOWN_MS
        if self._rng.random() > MOVE_CHANCE:
            return None
        return _MOOD_MOVES.get(self.mood)
