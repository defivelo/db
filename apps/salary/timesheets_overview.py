import enum

from django.contrib.auth import get_user_model
from django.db.models import F, FloatField, IntegerField, Q, Sum
from django.db.models.functions import Cast
from django.db.models.query import QuerySet

from rolepermissions.checkers import has_permission

from apps.challenge.models.session import Session
from apps.common import DV_STATES
from apps.salary.models import Timesheet
from defivelo.roles import user_cantons


class TimesheetStatus(enum.IntFlag):
    TIMESHEET_MISSING = 1
    TIMESHEET_NOT_VALIDATED = 2
    TIMESHEET_VALIDATED = 4

    def __str__(self):
        return str(self.value)


User = get_user_model()


def timesheets_validation_status(year, month=None, cantons=DV_STATES):
    """
    Get timesheets validation status matrix, a {'canton': status} dict
    if month is None, calculate for the full year
    The status is:
    - True for "all timesheets validated"
    - False for "missing timesheet validations"
    - None for "No sessions in that year-month, for that canton
    """
    months = range(1, 13)
    if month:
        months = [month]

    user_cache_key = "-".join(cantons)
    if user_cache_key not in timesheets_validation_status.all_users:
        timesheets_validation_status.all_users[user_cache_key] = (
            get_user_model()
            .objects.filter(profile__affiliation_canton__in=cantons)
            .prefetch_related("profile")
        )

    users = timesheets_validation_status.all_users[user_cache_key]

    statuses = {}

    for month_in_loop in months:
        sessions = Session.objects.filter(
            day__year=year, day__month=month_in_loop
        ).prefetch_related(
            "qualifications",
            "qualifications__leader",
            "qualifications__helpers",
            "qualifications__actor",
        )
        timesheets = get_timesheets(year=year, month=month_in_loop, users=users)

        sessions_by_user = regroup_sessions_by_user(sessions, users)
        timesheets_by_user = regroup_timesheets_by_user(timesheets)
        timesheets_statuses_by_canton = {
            canton: [
                get_timesheets_status_flags_for_user(
                    user=user,
                    sessions=sessions_by_user[user.pk],
                    timesheets=timesheets_by_user.get(user.pk, set()),
                    month_range=[month_in_loop],
                )[0]
                for user in users
                if user.profile.affiliation_canton == canton
                and user.pk in sessions_by_user
            ]
            for canton in cantons
        }
        are_all_timesheets_validated_in_month = {
            canton: all(
                [flag == TimesheetStatus.TIMESHEET_VALIDATED for flag in all_flags]
            )
            if len(all_flags)
            else None
            for canton, all_flags in timesheets_statuses_by_canton.items()
        }
        statuses[month_in_loop] = are_all_timesheets_validated_in_month

    if month:
        return statuses[month_in_loop]
    return statuses


timesheets_validation_status.all_users = {}


def get_orphaned_timesheets_per_month(year, users, month=None, cantons=DV_STATES):
    """
    Get orphaned timesheets validation status matrix, a {'canton': status} dict
    if month is None, calculate for the full year
    """
    months = range(1, 13)
    if month:
        months = [month]

    if not cantons:
        cantons = DV_STATES

    orphaned_timesheets_year = {}

    for month_in_loop in months:
        sessions = Session.objects.filter(
            day__year=year, day__month=month_in_loop
        ).prefetch_related(
            "qualifications",
            "qualifications__leader",
            "qualifications__helpers",
            "qualifications__actor",
        )
        timesheets = get_timesheets(year=year, month=month_in_loop, users=users)

        sessions_by_user = regroup_sessions_by_user(sessions, users)
        timesheets_by_user = regroup_timesheets_by_user(timesheets)
        orphaned_timesheets_month = set()
        for user in users:
            try:
                if user.profile.affiliation_canton in cantons:
                    orphaned_timesheets_month.update(
                        get_timesheets_without_corresponding_session(
                            sessions_by_user.get(user.pk, set()),
                            timesheets_by_user.get(user.pk, set()),
                        )
                    )
            except User.profile.RelatedObjectDoesNotExist as e:
                pass

        orphaned_timesheets_year[month_in_loop] = orphaned_timesheets_month

    if month:
        return orphaned_timesheets_year[month_in_loop]
    return orphaned_timesheets_year


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


def get_timesheets_status_flags_for_user(
    user, sessions, timesheets, month_range=range(1, 13)
):
    """
    Return a list of `TimesheetStatus` for the given `user`, `sessions` and
    `timesheets`. The list always contains 12 elements, one for each month (or for a selection of months)
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

    return [_get_flags(month) for month in month_range]


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


def get_timesheets_without_corresponding_session(sessions, timesheets):
    """
    Return a set of timesheets without a session in the corresponding day
    """
    session_days = [session.day for session in sessions]
    return set(
        timesheet for timesheet in timesheets if timesheet.date not in session_days
    )


def get_timesheets(year, users, month=None):
    """
    Return the timesheets of the given `users` for the given `year` (and eventually `month`).
    """
    kwargs = {"date__year": year, "user__in": users}
    if month:
        kwargs["date__month"] = month
    return Timesheet.objects.filter(**kwargs)


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

    if has_permission(user, "cantons_all"):
        qs = User.objects.all()
    elif has_permission(user, "cantons_mine"):
        cantons = user_cantons(user)
        qs = User.objects.filter(
            Q(profile__affiliation_canton__in=cantons) | Q(pk=user.pk)
        )
    else:
        qs = User.objects.filter(pk=user.pk)

    return qs.prefetch_related("profile")


def get_users_with_missing_timesheets(year: int, month: int, users):
    return [
        user
        for user, flags in get_timesheets_status_matrix(year, users).items()
        if flags[month - 1] & TimesheetStatus.TIMESHEET_MISSING
    ]


def get_missing_timesheet_status_per_month(timesheets_status_matrix):
    """
    Return a list of booleans (one per month) that indicate if any user has missing
    timesheets for each month.
    """
    return [
        any(
            statuses[month_index] & TimesheetStatus.TIMESHEET_MISSING
            for _, statuses in timesheets_status_matrix.items()
        )
        for month_index in range(0, 12)
    ]


def get_salary_details_list(object_list: QuerySet) -> QuerySet:
    """
    Return the queryset of salary details needed in multiple exports
    """

    # Django queries to convert the ignore Bool (0 if not ignored, 1 if ignored)
    # into an included Bool (1 if taken into account, 0 if ignored)
    included = 1 - Cast(F("ignore"), IntegerField())
    included_float = Cast(included, FloatField())

    return object_list.values("user").annotate(
        employee_code=F("user__profile__employee_code"),
        last_name=F("user__last_name"),
        first_name=F("user__first_name"),
        time_helper=Sum(F("time_helper") * included_float),
        actor_count=Sum(F("actor_count") * included),
        leader_count=Sum(F("leader_count") * included),
        overtime=Sum(F("overtime") * included_float),
        traveltime=Sum(F("traveltime") * included_float),
    )
