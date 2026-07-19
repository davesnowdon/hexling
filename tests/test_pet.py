import pet
from pet import Pet


class AlwaysMove:
    """rng stub whose random() always passes the MOVE_CHANCE check."""

    def random(self):
        return 0.0


def test_needs_decay_while_awake():
    p = Pet()
    food, fun, rest = p.food, p.fun, p.rest
    p.tick(10_000)
    assert p.food < food
    assert p.fun < fun
    assert p.rest < rest


def test_feed_raises_food_and_clamps():
    p = Pet()
    p.food = 0.9
    p.feed()
    assert p.food == 1.0


def test_falls_asleep_when_exhausted_and_wakes_recovered():
    p = Pet(rng=AlwaysMove())
    p.rest = pet.ASLEEP_BELOW / 2
    p.tick(1)
    assert p.asleep
    assert p.mood == pet.MOOD_ASLEEP
    # Sleep long enough to recover past the wake threshold.
    p.tick(60_000)
    assert not p.asleep
    assert p.rest > pet.WAKE_ABOVE


def test_stroke_wakes_and_cheers_up():
    p = Pet()
    p.asleep = True
    p.fun = 0.5
    p.stroke()
    assert not p.asleep
    assert p.fun > 0.5


def test_hunger_outranks_boredom():
    p = Pet()
    p.food = 0.1
    p.fun = 0.1
    assert p.mood == pet.MOOD_HUNGRY


def test_happy_when_fed_and_entertained():
    p = Pet()
    p.food = 1.0
    p.fun = 1.0
    assert p.mood == pet.MOOD_HAPPY


def test_suggest_move_respects_cooldown():
    p = Pet(rng=AlwaysMove())
    p.food = 1.0
    p.fun = 1.0
    p.tick(pet.MOVE_COOLDOWN_MS + 1)
    assert p.suggest_move() == "wiggle"
    # Cooldown was reset by the suggestion; nothing until it elapses.
    assert p.suggest_move() is None
    p.tick(pet.MOVE_COOLDOWN_MS + 1)
    assert p.suggest_move() == "wiggle"


def test_no_moves_while_asleep():
    p = Pet(rng=AlwaysMove())
    p.tick(pet.MOVE_COOLDOWN_MS + 1)
    p.asleep = True
    assert p.suggest_move() is None
