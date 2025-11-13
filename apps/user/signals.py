import queue
import threading

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.signals import request_finished
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from apps.user.models import UserProfile

# Global dictionary to store field changes temporarily during the save process
_user_changes = {}  # Payload indexed by user.pk
_user_changes_lock = threading.Lock()
_userprofile_to_notify = queue.Queue()  # User model that are used in user_changes.


@receiver(pre_save, sender=get_user_model())
def user_email_change_signal(sender, instance, **kwargs):
    """
    Signal to detect email changes on the User model
    Compute _user_changes if the email changes
    """
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.email != instance.email:
            # Store email change in global dictionary
            user_id = instance.pk
            with _user_changes_lock:
                _user_changes.setdefault(user_id, []).append(
                    {
                        "field": "email",
                        "old_value": old_instance.email,
                        "new_value": instance.email,
                    }
                )
    except sender.DoesNotExist:
        pass


@receiver(pre_save, sender=UserProfile)
def userprofile_field_change_signal(sender, instance, **kwargs):
    """
    Signal to detect changes on specific fields of the UserProfile model
    Compute _user_changes if the fields changes.
    """

    def normalize_iban_value(value):
        """The display format for IBAN has a space every 4 characters."""
        if value is None:
            return value
        grouping = 4
        value = value.upper().replace(" ", "").replace("-", "")
        return " ".join(value[i : i + grouping] for i in range(0, len(value), grouping))

    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        changes = []

        # Check IBAN changes,
        # - oldvalue is stored without space, and new one with some space, so we normalize the value
        old_iban = normalize_iban_value(old_instance.iban)
        new_iban = normalize_iban_value(instance.iban)
        if old_iban != new_iban and str(old_iban).strip():
            changes.append(
                {
                    "field": "IBAN",
                    "old_value": old_iban,
                    "new_value": new_iban,
                }
            )

        # Check address field changes
        address_fields = [
            "address_street",
            "address_no",
            "address_additional",
            "address_zip",
            "address_city",
            "address_canton",
        ]
        for field in address_fields:
            old_value = getattr(old_instance, field)
            new_value = getattr(instance, field)
            if old_value != new_value and str(old_value).strip():
                changes.append(
                    {"field": field, "old_value": old_value, "new_value": new_value}
                )

        # Store changes in global dictionary
        if changes:
            user_id = instance.user.pk
            with _user_changes_lock:
                _user_changes.setdefault(user_id, []).extend(changes)

    except sender.DoesNotExist:
        pass


@receiver(post_save, sender=get_user_model())
@receiver(post_save, sender=UserProfile)
def userprofile_mark_save_notification(sender, instance, **kwargs):
    """
    On post save, mark the user to be processed with changes given there is a payload with change for this user.
    """
    user = instance if sender == get_user_model() else instance.user

    if user:
        try:
            with _user_changes_lock:
                if user.pk in _user_changes:
                    _userprofile_to_notify.put_nowait(user)
        except queue.Full:
            pass


@receiver(request_finished)
def do_userprofile_notification(**kwargs):
    """
    On request finished, we regroup all changes by user and send an email.
    We loop on _userprofile_to_notify to know the user and on _user_changes for the payload.
    """
    while not _userprofile_to_notify.empty():
        try:
            user = _userprofile_to_notify.get_nowait()
            with _user_changes_lock:
                changes = _user_changes.pop(user.pk, {})
            _send_field_change_notification(user, changes)
        except queue.Empty:
            break


def _send_field_change_notification(user, changes):
    """
    Send an email notification with all field changes for a user
    """
    if not changes or not settings.PROFILE_CHANGED_NOTIFY_EMAIL:
        return

    # Prepare email content
    subject = _("Notification de modification de données utilisateur·trice")

    # Build the email body
    body_lines = [
        _("Bonjour,"),
        "",
        _(
            "Les informations suivantes pour l’utilisateur·trice {user} / {user_id} ont été modifiées:"
        ).format(user=user.get_full_name(), user_id=user.pk),
        "",
        "",
    ]

    for change in changes:
        field_name = change["field"]
        old_val = change["old_value"] or _("(vide)")
        new_val = change["new_value"] or _("(vide)")
        body_lines.append(f"• {field_name}: {old_val} → {new_val}")

    body_lines.extend(
        [
            "",
            _("Ceci est un message automatique."),
            _("Merci de mettre à jour la base de données des salaires en conséquences"),
        ]
    )

    body = "\n".join([str(b) for b in body_lines])

    # Send email to administrators or relevant recipients
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            list(filter(None, settings.PROFILE_CHANGED_NOTIFY_EMAIL.split(","))),
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send field change notification email: {e}")
