import signal
from argparse import Namespace

import pytest

from scripts import validate_clock


def test_pause_controller_always_resumes_verified_parent_after_interruption(monkeypatch):
    sent = []
    monkeypatch.setattr(validate_clock.os, "kill", lambda pid, sig: sent.append((pid, sig)))

    def interrupted_sleep(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(validate_clock.time, "sleep", interrupted_sleep)
    with pytest.raises(KeyboardInterrupt):
        validate_clock.pause_parent({"runtime_info": {"backend": "process", "process_pid": 999999}}, 999999, .35)
    assert sent == [(999999, signal.SIGSTOP), (999999, signal.SIGCONT)]


@pytest.mark.parametrize("backend,pid", [("event_loop", 999999), ("process", 111111)])
def test_pause_controller_refuses_wrong_backend_or_pid_without_signals(monkeypatch, backend, pid):
    sent = []
    monkeypatch.setattr(validate_clock.os, "kill", lambda *args: sent.append(args))
    with pytest.raises(ValueError, match="verified local HTTP parent"):
        validate_clock.pause_parent({"runtime_info": {"backend": backend, "process_pid": pid}}, 999999, .35)
    assert sent == []


def test_validation_rejects_previous_clock_mode_before_starting_controls(monkeypatch):
    monkeypatch.setattr(validate_clock, "read_state", lambda _: {
        "runtime_info": {"backend": "process", "process_pid": 999999, "clock_mode": "fixed_step_wall_clock"}})
    with pytest.raises(ValueError, match="clock mode"):
        validate_clock.run(Namespace(url="http://127.0.0.1:8765", parent_pid=999999,
                                     clock_mode="fixed_step_native_sleeper"))
