import json
from urllib.parse import parse_qs, urlparse

from django.forms import ValidationError
from django.urls import reverse
from django.utils import timezone

import pytest
from rolepermissions.roles import assign_role

from apps.user import FORMATION_M1
from apps.user.models import (
    USERSTATUS_ACTIVE,
    USERSTATUS_INACTIVE,
    UserManagedState,
    UserProfile,
)
from apps.user.tests.factories import UserFactory
from apps.user.views.standard import ReturnUrlMixin
from defivelo.tests.utils import (
    AuthClient,
    CollaboratorAuthClient,
    PowerUserAuthClient,
    StateManagerAuthClient,
)

pytestmark = pytest.mark.django_db


def login_capable(user):
    user.is_active = True
    user.set_password("secret")
    user.save()
    return UserProfile.objects.get(pk=user.pk).user


def listed_ids(response):
    return {u.pk for u in response.context["users"]}


def test_add_return_url_keeps_existing_query():
    url = ReturnUrlMixin._add_return_url("/fr/user/1/?a=1#frag", "/fr/season/")
    parsed = urlparse(url)

    assert parsed.path == "/fr/user/1/"
    assert parsed.fragment == "frag"
    assert parse_qs(parsed.query) == {"a": ["1"], "returnUrl": ["/fr/season/"]}


def test_detail_exposes_return_url_and_label():
    client = AuthClient()

    response = client.get(
        reverse("profile-detail"),
        {"returnUrl": "/fr/season/", "returnLabel": "Saison"},
    )

    assert response.context["return_url"] == "/fr/season/"
    assert response.context["return_label"] == "Saison"


def test_detail_ignores_foreign_return_url():
    client = AuthClient()

    response = client.get(
        reverse("profile-detail"),
        {"returnUrl": "https://evil.example.com/", "returnLabel": "Evil"},
    )

    assert response.context["return_url"] is None
    assert response.context["return_label"] is None


def test_update_redirects_with_return_url_and_label():
    client = AuthClient()
    url = reverse("user-update", kwargs={"pk": client.user.pk})

    response = client.post(
        url + "?returnLabel=Saison",
        {
            "first_name": "Jeanne",
            "last_name": "Doe",
            "language": "fr",
            "returnUrl": "/fr/season/",
        },
    )

    assert response.status_code == 302
    parsed = urlparse(response["Location"])
    assert parsed.path == reverse("profile-detail")
    assert parse_qs(parsed.query) == {
        "returnUrl": ["/fr/season/"],
        "returnLabel": ["Saison"],
    }
    client.user.refresh_from_db()
    assert client.user.first_name == "Jeanne"


def test_create_redirects_to_new_user_detail():
    client = PowerUserAuthClient()

    response = client.post(
        reverse("user-create"),
        {
            "first_name": "New",
            "last_name": "Person",
            "email": "new.person@example.com",
            "language": "fr",
            "status": USERSTATUS_ACTIVE,
            "nationality": "CH",
            "marital_status": 0,
            "bagstatus": 0,
        },
    )

    assert response.status_code == 302, response.context["form"].errors
    new = UserProfile.objects.get(user__email="new.person@example.com").user
    assert response["Location"] == reverse("user-detail", kwargs={"pk": new.pk})


def test_list_filters_by_language():
    client = PowerUserAuthClient()
    fr = UserFactory(profile__language="fr")
    de = UserFactory(profile__language="de")

    response = client.get(reverse("user-list"), {"profile__language": ["de"]})

    assert de.pk in listed_ids(response)
    assert fr.pk not in listed_ids(response)


def test_list_filters_by_challenge_languages():
    client = PowerUserAuthClient()
    main_it = UserFactory(profile__language="it")
    challenge_it = UserFactory(
        profile__language="fr", profile__languages_challenges=["it"]
    )
    other = UserFactory(profile__language="de")

    response = client.get(
        reverse("user-list"), {"profile__languages_challenges": ["it"]}
    )

    ids = listed_ids(response)
    assert {main_it.pk, challenge_it.pk} <= ids
    assert other.pk not in ids


def test_list_filters_by_cantons():
    client = PowerUserAuthClient()
    affiliated = UserFactory(profile__affiliation_canton="GE")
    mobile = UserFactory(
        profile__affiliation_canton="VD", profile__activity_cantons=["GE"]
    )
    other = UserFactory(profile__affiliation_canton="NE")

    response = client.get(reverse("user-list"), {"profile__activity_cantons": ["GE"]})

    ids = listed_ids(response)
    assert {affiliated.pk, mobile.pk} <= ids
    assert other.pk not in ids


def test_list_filters_without_role():
    client = PowerUserAuthClient()
    norole = UserFactory(profile__formation="")
    collaborator = UserFactory()

    response = client.get(reverse("user-list"), {"roles": ["0"]})

    ids = listed_ids(response)
    assert norole.pk in ids
    assert collaborator.pk not in ids
    assert client.user.pk not in ids


def test_list_filters_by_role():
    client = PowerUserAuthClient()
    collaborator = UserFactory()

    response = client.get(reverse("user-list"), {"roles": ["power_user"]})

    ids = listed_ids(response)
    assert client.user.pk in ids
    assert collaborator.pk not in ids


def test_list_filters_by_updated_at():
    client = PowerUserAuthClient()
    old = UserFactory()
    UserProfile.objects.filter(pk=old.pk).update(
        updated_at=timezone.now() - timezone.timedelta(days=400)
    )
    recent = UserFactory()

    response = client.get(
        reverse("user-list"),
        {"profile__updated_at": timezone.now().date().strftime("%d.%m.%Y")},
    )

    ids = listed_ids(response)
    assert recent.pk in ids
    assert old.pk not in ids


def test_list_wide_search():
    client = PowerUserAuthClient()
    found = UserFactory(first_name="Zéphyrine")
    other = UserFactory(first_name="Bob")

    response = client.get(reverse("user-list"), {"q": "zephyrine"})

    ids = listed_ids(response)
    assert found.pk in ids
    assert other.pk not in ids


def test_mark_inactive_lists_and_updates_monitors_without_role():
    client = PowerUserAuthClient()
    collaborator = UserFactory()
    norole = UserFactory(profile__formation="")
    UserProfile.objects.filter(pk=norole.pk).update(formation=FORMATION_M1)
    url = reverse("users-actions-markinactive")

    response = client.get(url)

    affected = {p.pk for p in response.context["affected_accounts"]}
    assert norole.pk in affected
    assert collaborator.pk not in affected

    response = client.post(url)

    assert response.status_code == 302
    norole_profile = UserProfile.objects.get(pk=norole.pk)
    assert norole_profile.status == USERSTATUS_INACTIVE
    assert norole_profile.status_updatetime is not None
    assert UserProfile.objects.get(pk=collaborator.pk).status == USERSTATUS_ACTIVE


def test_mark_inactive_forbidden_for_state_manager():
    client = StateManagerAuthClient()

    response = client.get(reverse("users-actions-markinactive"))

    assert response.status_code == 403


def ac_ids(response):
    return {int(r["id"]) for r in response.json()["results"]}


def test_coordinators_autocomplete():
    client = PowerUserAuthClient()
    coordinator = UserFactory(profile__formation="")
    assign_role(coordinator, "coordinator")
    other = UserFactory()

    response = client.get(reverse("user-coordinators"))

    ids = ac_ids(response)
    assert coordinator.pk in ids
    assert other.pk not in ids


def test_persons_relevant_for_sessions_filters_by_forwarded_cantons():
    client = PowerUserAuthClient()
    in_canton = UserFactory(profile__affiliation_canton="GE")
    mobile = UserFactory(
        profile__affiliation_canton="VD", profile__activity_cantons=["GE"]
    )
    elsewhere = UserFactory(profile__affiliation_canton="NE")

    response = client.get(
        reverse("user-PersonsRelevantForSessions-ac"),
        {"forward": json.dumps({"cantons": ["GE"]})},
    )

    ids = ac_ids(response)
    assert {in_canton.pk, mobile.pk} <= ids
    assert elsewhere.pk not in ids


def test_helpers_autocomplete_label_has_formation():
    client = PowerUserAuthClient()
    helper = UserFactory(first_name="Ann", last_name="Helper")

    response = client.get(reverse("user-Helpers-ac"))

    labels = {int(r["id"]): r["text"] for r in response.json()["results"]}
    assert labels[helper.pk] == "Ann Helper M1"


def test_sendcredentials_forbidden_for_foreign_canton():
    client = StateManagerAuthClient()
    foreign = UserFactory(profile__affiliation_canton="GE")
    UserManagedState.objects.filter(user=client.user).update(canton="VD")

    response = client.get(reverse("user-sendcredentials", kwargs={"pk": foreign.pk}))

    assert response.status_code == 403


def test_resendcredentials_forbidden_when_never_sent():
    client = PowerUserAuthClient()
    user = UserFactory()

    response = client.get(reverse("user-resendcredentials", kwargs={"pk": user.pk}))

    assert response.status_code == 403


def test_state_manager_cannot_remove_coordinator_role():
    client = StateManagerAuthClient()
    coordinator = login_capable(UserFactory(profile__formation=""))
    assign_role(coordinator, "coordinator")

    with pytest.raises(ValidationError):
        client.post(
            reverse("user-assign-role", kwargs={"pk": coordinator.pk}),
            {"role": ""},
        )


@pytest.mark.xfail(
    reason="UserAssignRole.dispatch returns None instead of raising PermissionDenied "
    "when the requester lacks permissions (apps/user/views/credentials.py:109-115)",
    raises=AttributeError,
    strict=True,
)
def test_assign_role_forbidden_without_permission():
    client = CollaboratorAuthClient()
    other = login_capable(UserFactory())

    response = client.get(reverse("user-assign-role", kwargs={"pk": other.pk}))

    assert response.status_code == 403


def test_return_url_mixin_success_url_prefers_return_url():
    class Base:
        def get_success_url(self):
            return "/default/"

    class View(ReturnUrlMixin, Base):
        def __init__(self, return_url):
            self.return_url = return_url

        def get_return_url(self):
            return self.return_url

    assert View("/back/").get_success_url() == "/back/"
    assert View(None).get_success_url() == "/default/"


def test_list_empty_multi_filters_do_not_restrict():
    client = PowerUserAuthClient()
    user = UserFactory(profile__language="de", profile__affiliation_canton="GE")

    response = client.get(
        reverse("user-list"),
        {
            "profile__language": [""],
            "profile__languages_challenges": [""],
            "profile__activity_cantons": [""],
        },
    )

    assert user.pk in listed_ids(response)
