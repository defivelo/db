from datetime import timedelta


def _get_qualifs_calendar_structured_data(our_sessions):
    """
    Alternative to mixins and parent class mess
    """
    date_sessions = []

    # Get to its monday (see https://stackoverflow.com/questions/1622038/find-mondays-date-with-python)
    first_session_day = our_sessions[0].day
    first_monday = first_session_day + timedelta(days=-first_session_day.weekday())
    thisday = first_monday
    offset = 0
    while len(our_sessions) > 0:
        thisday = first_monday + timedelta(days=offset)
        struct = {"day": thisday, "sessions": []}
        while our_sessions and our_sessions[0].day == thisday:
            struct["sessions"].append(our_sessions.pop(0))
        date_sessions.append(struct)
        # Go to next day
        offset = offset + 1
    # Fill in the missing days
    while thisday.weekday() != 6:
        thisday = first_monday + timedelta(days=offset)
        date_sessions.append({"day": thisday, "sessions": []})
        offset = offset + 1
    return date_sessions
