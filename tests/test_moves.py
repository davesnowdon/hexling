from moves import MOVES, MoveRunner


def test_idle_runner_returns_none():
    runner = MoveRunner()
    assert not runner.active
    assert runner.tick(50) is None


def test_unknown_move_is_ignored():
    runner = MoveRunner()
    runner.start("moonwalk")
    assert not runner.active


def test_steps_play_in_order():
    runner = MoveRunner()
    runner.start("shuffle")  # 300/200/300/200 ms
    motors, servos = runner.tick(100)
    assert motors == (0.5, 0.5)
    assert servos is None
    motors, _ = runner.tick(250)  # 350ms in: second step (stopped)
    assert motors == (0.0, 0.0)


def test_slow_frame_skips_whole_steps():
    runner = MoveRunner()
    runner.start("shuffle")
    motors, _ = runner.tick(999)  # lands in the final step
    assert motors == (0.0, 0.0)
    assert runner.tick(2) is None
    assert not runner.active


def test_stop_cancels_mid_move():
    runner = MoveRunner()
    runner.start("wiggle")
    runner.tick(100)
    runner.stop()
    assert not runner.active
    assert runner.tick(50) is None


def test_all_scripts_are_well_formed():
    for name, steps in MOVES.items():
        assert steps, name
        for duration, motors, servos in steps:
            assert duration > 0, name
            if motors is not None:
                assert all(-1.0 <= m <= 1.0 for m in motors), name
            if servos is not None:
                assert all(-1000 <= s <= 1000 for s in servos), name
