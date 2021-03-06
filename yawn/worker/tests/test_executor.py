import pytest

from unittest import mock

import time

from .. import executor


@pytest.fixture()
def manager():
    return executor.Manager()


def test_read_output(manager):
    execution_id = 1
    command = 'echo starting && sleep 0.5 && echo stopping 1>&2'
    manager.start_subprocess(execution_id, command, environment={}, timeout=None)

    # stdout is ready
    results = manager.read_output(timeout=0.4)
    assert len(results) == 1
    assert results[0].stdout == 'starting\n'
    assert results[0].stderr is None
    assert results[0].returncode is None
    assert results[0].execution_id == execution_id

    # stderr is ready, stdout gets closed
    results = manager.read_output(timeout=1)
    assert len(results) == 1
    assert results[0].stdout is None
    assert results[0].stderr == 'stopping\n'
    assert results[0].returncode is None
    assert results[0].execution_id == execution_id

    # stderr gets closed and result is available
    results = manager.read_output()
    assert len(results) == 1
    assert results[0].stdout is None
    assert results[0].stderr is None
    assert results[0].returncode == 0
    assert results[0].execution_id == execution_id


def test_timeout(manager):
    command = 'sleep 10'
    manager.start_subprocess(1, command, environment={}, timeout=-1)

    manager.read_output()  # first read kills, but the pipes are still open

    results = manager.read_output()
    assert len(results) == 1
    assert results[0].stdout is None
    assert results[0].stderr is None
    assert results[0].returncode == -9


@mock.patch('yawn.worker.executor.os.killpg')
def test_timeout_already_exited(mock_kill, manager):
    command = 'true'
    manager.start_subprocess(1, command, environment={}, timeout=-1)

    results = manager.read_output(timeout=1)
    assert len(results) == 1
    assert results[0].stdout is None
    assert results[0].stderr is None
    assert results[0].returncode == 0

    assert mock_kill.call_count == 1


def test_mark_terminated(manager):
    execution_id = 1
    execution = executor.Execution(None, execution_id, None)
    manager.running[execution_id] = execution
    manager.mark_terminated([1, 2])
    assert execution.deadline <= time.monotonic()
