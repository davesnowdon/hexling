"""Hexling's face, drawn on the round 240x240 screen.

Everything here only touches the ctx passed in, so the module stays
importable off-badge.  Moods are the plain strings owned by pet.py.
"""

# Background and feature colours per mood (r, g, b in 0..1).
_PALETTE = {
    "asleep": ((0.05, 0.05, 0.15), (0.4, 0.4, 0.6)),
    "hungry": ((0.20, 0.08, 0.02), (1.0, 0.6, 0.2)),
    "bored": ((0.10, 0.10, 0.10), (0.6, 0.6, 0.6)),
    "happy": ((0.02, 0.15, 0.08), (0.3, 1.0, 0.5)),
    "content": ((0.02, 0.10, 0.15), (0.4, 0.8, 1.0)),
}
_DEFAULT = _PALETTE["content"]

_EYE_X = 45      # eye centres at (+/-_EYE_X, _EYE_Y)
_EYE_Y = -30
_EYE_R = 26
_PUPIL_R = 10

_BLINK_PERIOD_MS = 3500
_BLINK_LEN_MS = 150

_TWO_PI = 6.28318


def draw(ctx, mood, wall_ms):
    """Draw the whole face for the given mood.

    wall_ms is elapsed app time, used to animate blinks; the caller
    doesn't need it to mean anything in particular.
    """
    bg, fg = _PALETTE.get(mood, _DEFAULT)
    ctx.save()
    ctx.rgb(*bg).rectangle(-120, -120, 240, 240).fill()
    if mood == "asleep":
        _draw_closed_eyes(ctx, fg)
        _draw_zzz(ctx, fg, wall_ms)
    else:
        blinking = (wall_ms % _BLINK_PERIOD_MS) < _BLINK_LEN_MS
        for x in (-_EYE_X, _EYE_X):
            if blinking:
                _draw_eyelid(ctx, fg, x)
            else:
                _draw_eye(ctx, fg, x)
        _draw_mouth(ctx, fg, mood)
    ctx.restore()


def _draw_eye(ctx, fg, x):
    ctx.rgb(*fg).arc(x, _EYE_Y, _EYE_R, 0, _TWO_PI, True).fill()
    ctx.rgb(0, 0, 0).arc(x, _EYE_Y, _PUPIL_R, 0, _TWO_PI, True).fill()


def _draw_eyelid(ctx, fg, x):
    ctx.rgb(*fg).rectangle(x - _EYE_R, _EYE_Y - 3, 2 * _EYE_R, 6).fill()


def _draw_closed_eyes(ctx, fg):
    for x in (-_EYE_X, _EYE_X):
        _draw_eyelid(ctx, fg, x)


def _draw_mouth(ctx, fg, mood):
    ctx.rgb(*fg)
    ctx.line_width = 6
    if mood == "happy":
        # Smile: lower half of a circle above the mouth line.
        ctx.arc(0, 30, 35, 0.3, _TWO_PI / 2 - 0.3, False).stroke()
    elif mood == "hungry":
        # Open mouth.
        ctx.arc(0, 50, 18, 0, _TWO_PI, True).fill()
    elif mood == "bored":
        # Flat line.
        ctx.move_to(-30, 55).line_to(30, 55).stroke()
    else:
        # Content: small smile.
        ctx.arc(0, 40, 22, 0.4, _TWO_PI / 2 - 0.4, False).stroke()


def _draw_zzz(ctx, fg, wall_ms):
    # A "z" that drifts upward and repeats.
    phase = (wall_ms % 2000) / 2000.0
    ctx.rgb(*fg)
    ctx.font_size = 24
    ctx.move_to(60, int(20 - 60 * phase)).text("z")
    ctx.font_size = 16
    ctx.move_to(80, int(40 - 60 * phase)).text("z")


def draw_status(ctx, message):
    """One short dim line at the bottom of the screen (e.g. hardware
    hints).  Keep messages brief: the display is a 240px circle, so
    only ~150px of width fits at this height."""
    ctx.save()
    ctx.rgb(0.5, 0.5, 0.5)
    ctx.font_size = 14
    width = ctx.text_width(message)
    ctx.move_to(-width // 2, 88).text(message)
    ctx.restore()
