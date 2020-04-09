from django.db import migrations
from django.db.models import Count, Q
from django.utils import timezone


def update_timesheet_leader_count(session_model, timesheet):
    session_qs = (
        # Code duplicated from `apps.salary.views.UserMonthlyTimesheets.get_queryset`
        (
            session_model.objects.values("day")
            .filter(
                Q(qualifications__actor=timesheet.user)
                | Q(qualifications__helpers=timesheet.user)
                | Q(qualifications__leader=timesheet.user)
            )
            .filter(day__lte=timezone.now())
            .annotate(
                orga_count=Count("orga_id", distinct=True),
                helper_count=Count(
                    "qualifications__pk",
                    filter=Q(qualifications__helpers=timesheet.user)
                    | Q(qualifications__leader=timesheet.user),
                    distinct=True,
                ),
                leader_count=Count(
                    "qualifications__pk",
                    filter=Q(qualifications__leader=timesheet.user),
                    distinct=True,
                ),
                actor_count=Count(
                    "qualifications__pk",
                    filter=Q(qualifications__actor=timesheet.user),
                    distinct=True,
                ),
            )
        )
        .exclude(actor_count=0, helper_count=0)
        .order_by("day")
    )
    session = session_qs.get(day=timesheet.date)
    timesheet.leader_count = session["leader_count"]
    timesheet.save()


def update_timesheets(apps, schema_editor):
    Session = apps.get_model("challenge", "Session")
    Timesheet = apps.get_model("salary", "Timesheet")
    for timesheet in Timesheet.objects.all():
        update_timesheet_leader_count(Session, timesheet)


class Migration(migrations.Migration):

    dependencies = [
        ("salary", "0005_timesheet_leader_count"),
    ]

    operations = [
        migrations.RunPython(update_timesheets),
    ]
