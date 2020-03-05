from django import template

from ..timesheets_overview import TimesheetStatus

register = template.Library()


@register.filter
def timesheet_status_css_class(timesheet_status):
    """
    Given a `TimesheetStatus`, return a proper CSS class name to represent it.
    """
    if timesheet_status & TimesheetStatus.TIMESHEET_MISSING:
        return "danger"
    elif timesheet_status & TimesheetStatus.TIMESHEET_NOT_VALIDATED:
        return "warning"
    elif timesheet_status & TimesheetStatus.TIMESHEET_VALIDATED:
        return "success"

    return ""
