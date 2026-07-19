"""Find and drive a BadgeBot HexDrive hexpansion.

The pure parts (type table, slew-rate ramping, the HexDrive wrapper)
have no badge imports so they test headless with a stub app.  Only
find_hexdrive() touches badge hardware, and it imports lazily so this
module also imports under plain CPython.
"""

VID = 0xCAFE


class HexDriveType:
    def __init__(self, pid, motors=0, servos=0, name="Unknown"):
        self.pid = pid
        self.motors = motors
        self.servos = servos
        self.name = name


# The four HexDrive variants, keyed by hexpansion PID.
TYPES = {
    0xCBCB: HexDriveType(0xCBCB, motors=2, servos=4, name="2 Mot 4 Srvo"),
    0xCBCA: HexDriveType(0xCBCA, motors=2, name="2 Motor"),
    0xCBCC: HexDriveType(0xCBCC, servos=4, name="4 Servo"),
    0xCBCD: HexDriveType(0xCBCD, motors=1, servos=2, name="1 Mot 2 Srvo"),
}

MAX_POWER = 65535       # full-scale motor PWM duty
PWM_FREQ = 10000

# Slew limits per millisecond of elapsed time.  Ramping instead of
# stepping the outputs keeps the current draw within what the badge's
# boost converter can supply (same approach as the HexDriveUseTemplate,
# which steps 7500 duty per 10 ms tick).
MOTOR_SLEW_PER_MS = 750     # duty units: 0 -> full power in ~87 ms
SERVO_SLEW_PER_MS = 8       # microseconds: full swing in ~250 ms


def ramp(current, target, max_step):
    """Move current toward target by at most max_step (either sign)."""
    if current < target:
        return min(current + max_step, target)
    if current > target:
        return max(current - max_step, target)
    return current


class HexDrive:
    """Wraps a running HexDrive EEPROM app with target-based control.

    Set targets whenever you like; call tick(delta_ms) every frame to
    ramp the real outputs toward them.
    """

    def __init__(self, hexdrive_app, hd_type, port):
        self.app = hexdrive_app
        self.type = hd_type
        self.port = port
        self.powered = False
        self._motor_out = [0] * hd_type.motors
        self._motor_target = [0] * hd_type.motors
        self._servo_out = [0] * hd_type.servos
        self._servo_target = [0] * hd_type.servos

    def start(self):
        """Power up the HexDrive (boost converter on).  Returns True on
        success; False if its PWM resources are unavailable."""
        if not self.app.get_status():
            return False
        self.app.set_freq(PWM_FREQ)
        self.app.set_power(True)
        self.powered = True
        return True

    def stop(self):
        """Zero everything and power the HexDrive down."""
        self._motor_target = [0] * self.type.motors
        self._servo_target = [0] * self.type.servos
        self._motor_out = [0] * self.type.motors
        self._servo_out = [0] * self.type.servos
        if self.type.motors:
            self.app.set_motors(tuple(self._motor_out))
        if self.type.servos:
            self.app.set_servoposition()  # no args = all servos off
        self.app.set_power(False)
        self.powered = False

    def set_targets(self, motors=None, servos=None):
        """Set new output targets.

        motors: per-channel power fractions -1.0..1.0; servos: positions
        in microseconds about centre.  Values beyond the channels this
        variant has are ignored; None leaves that group's targets alone.
        """
        if motors is not None:
            for i in range(self.type.motors):
                frac = motors[i] if i < len(motors) else 0.0
                self._motor_target[i] = int(frac * MAX_POWER)
        if servos is not None:
            for i in range(self.type.servos):
                self._servo_target[i] = int(servos[i]) if i < len(servos) else 0

    def tick(self, delta_ms):
        """Ramp outputs toward their targets and push them out."""
        if not self.powered:
            return
        if self.type.motors:
            step = int(MOTOR_SLEW_PER_MS * delta_ms)
            self._motor_out = [
                ramp(out, target, step)
                for out, target in zip(self._motor_out, self._motor_target)
            ]
            self.app.set_motors(tuple(self._motor_out))
        if self.type.servos:
            step = int(SERVO_SLEW_PER_MS * delta_ms)
            for i in range(self.type.servos):
                new = ramp(self._servo_out[i], self._servo_target[i], step)
                if new != self._servo_out[i]:
                    self._servo_out[i] = new
                    self.app.set_servoposition(i, new)


def find_hexdrive():
    """Scan hexpansion ports 1-6 for a HexDrive running its EEPROM app.

    Returns a HexDrive wrapper for the first one found, or None.  Safe
    in the simulator, where the fake I2C bus never has an EEPROM.
    """
    from machine import I2C
    from system.hexpansion.util import detect_eeprom_addr, read_hexpansion_header

    for port in range(1, 7):
        try:
            i2c = I2C(port)
            addr, _ = detect_eeprom_addr(i2c)
        except Exception:
            continue
        if addr is None:
            continue
        try:
            header = read_hexpansion_header(i2c, addr)
        except Exception:
            continue
        if header is None or header.vid != VID:
            continue
        hd_type = TYPES.get(header.pid)
        if hd_type is None:
            continue
        hexdrive_app = _find_hexdrive_app(port)
        if hexdrive_app is None:
            print(f"Hexling: HexDrive on port {port} but its app is not running")
            continue
        print(f"Hexling: using {hd_type.name} HexDrive on port {port}")
        return HexDrive(hexdrive_app, hd_type, port)
    return None


def _find_hexdrive_app(port):
    """The running HexDrive EEPROM app for a port, or None."""
    from system.scheduler import scheduler

    for an_app in scheduler.apps:
        if (
            type(an_app).__name__ == "HexDriveApp"
            and getattr(getattr(an_app, "config", None), "port", None) == port
        ):
            return an_app
    return None
