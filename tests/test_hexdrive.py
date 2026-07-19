import pytest

from hexdrive import MAX_POWER, PWM_FREQ, TYPES, HexDrive, ramp


class FakeHexDriveApp:
    """Records the calls the HexDrive wrapper makes on the EEPROM app."""

    def __init__(self, status=True):
        self.status = status
        self.calls = []

    def get_status(self):
        return self.status

    def set_freq(self, freq):
        self.calls.append(("freq", freq))

    def set_power(self, on):
        self.calls.append(("power", on))

    def set_motors(self, outputs):
        self.calls.append(("motors", outputs))

    def set_servoposition(self, index=None, position=None):
        self.calls.append(("servo", index, position))


def make_hexdrive(pid=0xCBCB, status=True):
    fake = FakeHexDriveApp(status)
    return HexDrive(fake, TYPES[pid], port=1), fake


def test_ramp_moves_toward_target_and_stops_there():
    assert ramp(0, 100, 30) == 30
    assert ramp(90, 100, 30) == 100
    assert ramp(0, -100, 30) == -30
    assert ramp(5, 5, 30) == 5


def test_start_configures_and_powers_up():
    hd, fake = make_hexdrive()
    assert hd.start()
    assert hd.powered
    assert ("freq", PWM_FREQ) in fake.calls
    assert ("power", True) in fake.calls


def test_start_fails_without_pwm_resources():
    hd, _ = make_hexdrive(status=False)
    assert not hd.start()
    assert not hd.powered


def test_tick_ramps_motors_toward_target():
    hd, fake = make_hexdrive()
    hd.start()
    hd.set_targets(motors=(1.0, -1.0))
    hd.tick(10)
    motor_calls = [c for c in fake.calls if c[0] == "motors"]
    first = motor_calls[-1][1]
    assert 0 < first[0] < MAX_POWER
    assert first[1] == -first[0]
    # Enough ticks to converge on full power.
    for _ in range(20):
        hd.tick(10)
    assert [c for c in fake.calls if c[0] == "motors"][-1][1] == (MAX_POWER, -MAX_POWER)


def test_servo_only_variant_ignores_motor_targets():
    hd, fake = make_hexdrive(pid=0xCBCC)  # 4 Servo
    hd.start()
    hd.set_targets(motors=(1.0, 1.0), servos=(100, 0, 0, 0))
    hd.tick(5)
    assert not [c for c in fake.calls if c[0] == "motors"]
    assert ("servo", 0, 40) in fake.calls  # 8 us/ms * 5 ms


def test_extra_channels_in_targets_are_ignored():
    hd, _ = make_hexdrive(pid=0xCBCD)  # 1 motor + 2 servos
    hd.set_targets(motors=(0.5, 0.5), servos=(100, 100, 100, 100))
    assert len(hd._motor_target) == 1
    assert len(hd._servo_target) == 2


def test_stop_zeroes_and_powers_down():
    hd, fake = make_hexdrive()
    hd.start()
    hd.set_targets(motors=(1.0, 1.0))
    hd.tick(10)
    hd.stop()
    assert not hd.powered
    assert fake.calls[-3:] == [
        ("motors", (0, 0)),
        ("servo", None, None),
        ("power", False),
    ]


def test_unpowered_tick_is_a_noop():
    hd, fake = make_hexdrive()
    hd.set_targets(motors=(1.0, 1.0))
    hd.tick(10)
    assert not [c for c in fake.calls if c[0] == "motors"]
