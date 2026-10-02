from datetime import date
from types import SimpleNamespace

from apps.info.utils import _get_qualifs_calendar_structured_data


def _session(day):
    return SimpleNamespace(day=day)


def test_single_wednesday_session_fills_whole_week():
    session = _session(date(2030, 3, 6))
    result = _get_qualifs_calendar_structured_data([session])
    assert [d["day"] for d in result] == [date(2030, 3, d) for d in range(4, 11)]
    assert result[2]["sessions"] == [session]
    assert all(d["sessions"] == [] for i, d in enumerate(result) if i != 2)


def test_sessions_grouped_by_day_across_weeks():
    s1 = _session(date(2030, 3, 4))
    s2 = _session(date(2030, 3, 4))
    s3 = _session(date(2030, 3, 13))
    result = _get_qualifs_calendar_structured_data([s1, s2, s3])
    assert result[0]["day"] == date(2030, 3, 4)
    assert result[0]["sessions"] == [s1, s2]
    assert result[-1]["day"] == date(2030, 3, 17)
    assert len(result) == 14
    by_day = {d["day"]: d["sessions"] for d in result}
    assert by_day[date(2030, 3, 13)] == [s3]


def test_sunday_session_ends_on_that_sunday():
    session = _session(date(2030, 3, 10))
    result = _get_qualifs_calendar_structured_data([session])
    assert len(result) == 7
    assert result[-1] == {"day": date(2030, 3, 10), "sessions": [session]}


def test_input_list_is_consumed():
    sessions = [_session(date(2030, 3, 4))]
    _get_qualifs_calendar_structured_data(sessions)
    assert sessions == []
