from django import template

register = template.Library()


@register.filter
def field_type(field):
    """
    Get the name of the field class.
    """
    if hasattr(field, "field"):
        field = field.field
    s = str(type(field.widget).__name__)
    s = s.lower()
    return s
