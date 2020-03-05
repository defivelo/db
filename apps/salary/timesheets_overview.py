import enum

from django.contrib.auth import get_user_model
from django.db.models import Q

from rolepermissions.checkers import has_permission

from apps.challenge.models.session import Session
from apps.salary.models import Timesheet
from defivelo.roles import user_cantons


class TimesheetStatus(enum.IntFlag):
    TIMESHEET_MISSING = 1
    TIMESHEET_NOT_VALIDATED = 2
    TIMESHEET_VALIDATED = 4


def get_timesheets_status_matrix(year, users):
    """
    Return a dict of `{user: [TimesheetStatus]}` for all users who worked during the
    given `year`. Only users who `user` has access to (either because the user can see
    all cantons, or because they're affiliated in the canton the user manages) are
    returned.
    """
    sessions = Session.objects.filter(day__year=year).prefetch_related(
        "qualifications", "qualifications__helpers"
    )
    timesheets = get_timesheets(year=year, users=users)

    sessions_by_user = regroup_sessions_by_user(sessions, users)
    timesheets_by_user = regroup_timesheets_by_user(timesheets)

    timesheets_status_matrix = {
        user: get_timesheets_status_flags_for_user(
            user, sessions_by_user[user.pk], timesheets_by_user.get(user.pk, set())
        )
        for user in users
        if user.pk in sessions_by_user
    }

    return timesheets_status_matrix


def get_timesheets_status_flags_for_user(user, sessions, timesheets):
    """
    Return a list of `TimesheetStatus` for the given `user`, `sessions` and
    `timesheets`. The list always contains 12 elements, one for each month.
    """
    months_with_missing_timesheets = get_months_without_timesheets(sessions, timesheets)
    timesheets_by_month = regroup_timesheets_by_month(timesheets)

    def _get_flags(month):
        flags = 0

        if month in months_with_missing_timesheets:
            flags |= TimesheetStatus.TIMESHEET_MISSING

        for timesheet in timesheets_by_month.get(month, []):
            if timesheet.validated_at:
                flags |= TimesheetStatus.TIMESHEET_VALIDATED
            elif not timesheet.validated_at:
                flags |= TimesheetStatus.TIMESHEET_NOT_VALIDATED

        return flags

    return [_get_flags(month) for month in range(1, 13)]


def regroup_sessions_by_user(sessions, users):
    """
    Regroup the given `Session` queryset by user (only keeping users in `users`) and
    return a dict `{user_id: {session1, session2, ...}}`.
    """
    sessions_by_user = {}
    users_ids = {user.pk for user in users}

    for session in sessions:
        for qualification in session.qualifications.all():
            if qualification.leader_id and qualification.leader_id in users_ids:
                sessions_by_user.setdefault(qualification.leader_id, set()).add(session)

            if qualification.actor_id and qualification.actor_id in users_ids:
                sessions_by_user.setdefault(qualification.actor_id, set()).add(session)

            for helper in qualification.helpers.all():
                if helper.pk in users_ids:
                    sessions_by_user.setdefault(helper.pk, set()).add(session)

    return sessions_by_user


def regroup_timesheets_by_user(timesheets):
    """
    Regroup the given `Timesheet` queryset by user and return a dict `{user_id:
    {timesheet1, timesheet2, ...}}`.
    """
    timesheets_by_user = {}

    for timesheet in timesheets:
        timesheets_by_user.setdefault(timesheet.user_id, set()).add(timesheet)

    return timesheets_by_user


def regroup_timesheets_by_month(timesheets):
    """
    Regroup the given `Timesheet` queryset by month and return a dict of `{month:
    [timesheets]}`, where `month` is a month number (1 - 12) and `timesheets` the list
    of associated timesheets.
    """
    timesheets_by_month = {}
    for timesheet in timesheets:
        timesheets_by_month.setdefault(timesheet.date.month, []).append(timesheet)

    return timesheets_by_month


def get_months_without_timesheets(sessions, timesheets):
    """
    Return a set of month numbers (1 - 12) that have sessions that don't have any
    associated timesheet.
    """
    days_with_missing_timesheets = set(session.day for session in sessions) - set(
        timesheet.date for timesheet in timesheets
    )

    return {date.month for date in days_with_missing_timesheets}


def get_timesheets(year, users):
    """
    Return the timesheets of the given `users` for the given `year`.
    """
    return Timesheet.objects.filter(date__year=year, user__in=users)


def get_timesheets_amount_by_month(year, users):
    """
    Return the total amount of timesheets for the given year and the given users, as a
    list of 12 elements, 0 being January and 11 being December.
    """
    timesheets_by_month = regroup_timesheets_by_month(
        get_timesheets(year=year, users=users)
    )

    total_by_month = [
        sum(
            timesheet.get_total_amount() for timesheet in timesheets_by_month.get(i, [])
        )
        for i in range(1, 13)
    ]

    return total_by_month


def get_visible_users(user):
    """
    Return a queryset of `User` objects the given `user` has access to.
    """
    User = get_user_model()

    if has_permission(user, "cantons_all"):
        qs = User.objects.all()
    elif has_permission(user, "cantons_mine"):
        cantons = user_cantons(user)
        qs = User.objects.filter(
            Q(profile__affiliation_canton__in=cantons) | Q(pk=user.pk)
        )
    else:
        qs = User.objects.filter(pk=user.pk)

    return qs
