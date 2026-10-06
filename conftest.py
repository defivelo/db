import pytest


@pytest.fixture(autouse=True)
def _reset_user_change_notifications():
    """
    User and profile saves queue change notifications that are only sent and
    flushed on request_finished; don't let them leak into the next test.
    """
    from apps.user import signals

    def reset():
        signals._user_changes.clear()
        while not signals._userprofile_to_notify.empty():
            signals._userprofile_to_notify.get_nowait()

    reset()
    yield
    reset()
