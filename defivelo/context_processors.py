from django.utils import timezone


def now(request):
    return {"now": timezone.now()}
