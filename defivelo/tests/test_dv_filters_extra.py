import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django import forms
from django.core.exceptions import PermissionDenied
from django.utils.translation import override

import pytest

from apps.challenge import (
    AVAILABILITY_FIELDKEY,
    CHOICE_FIELDKEY,
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
    CONFLICT_FIELDKEY,
    SEASON_WORKWISH_FIELDKEY,
    STAFF_FIELDKEY,
    SUPERLEADER_FIELDKEY,
)
from apps.challenge.tests.factories import (
    QualificationFactory,
    SeasonFactory,
    SessionFactory,
)
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING, DV_STATES
from apps.orga.tests.factories import OrganizationFactory
from apps.user.tests.factories import UserFactory
from defivelo.templatetags import dv_filters

USER = SimpleNamespace(pk=7)
SPK = 42


def key(fmt, spk=SPK):
    return fmt.format(hpk=USER.pk, spk=spk)


def test_format_phone_number_empty():
    assert dv_filters._format_phone_numer("") == ""
    assert dv_filters._format_phone_numer(None) == ""


def test_tel_int():
    assert dv_filters.tel_int("") == ""
    assert dv_filters.tel_int("+41791234567") == "+41791234567"
    assert dv_filters.tel_int("079 123 45 67") == "+41791234567"


def test_profile_tag_empty():
    assert dv_filters.profile_tag(None) == ""


def test_profile_tag_with_natel(db):
    user = UserFactory(first_name="Ann", last_name="Lee", profile__natel="0791234567")

    tag = dv_filters.profile_tag(user)

    assert tag.startswith("<span>Ann Lee<br /><small>")
    assert 'href="tel:+41791234567"' in tag


def test_profile_tag_restricted_hides_natel(db):
    user = UserFactory(first_name="Ann", last_name="Lee", profile__natel="0791234567")

    assert dv_filters.profile_tag(user, True) == "<span>Ann Lee</span>"


class AvailForm(forms.Form):
    def __init__(self, fieldkeys, **kwargs):
        super().__init__(**kwargs)
        for fieldkey in fieldkeys:
            self.fields[fieldkey] = forms.CharField(initial="x")


def test_useravailsessions_renders_matching_fields():
    form = AvailForm(
        [
            SEASON_WORKWISH_FIELDKEY.format(hpk=USER.pk),
            key(AVAILABILITY_FIELDKEY),
            AVAILABILITY_FIELDKEY.format(hpk=99, spk=SPK),
        ]
    )

    output = dv_filters.useravailsessions(form, USER)

    assert output.count("<td>") == 2
    assert 'id="season-ww-h7"' in output
    assert f'id="avail-h7-s{SPK}"' in output
    assert "avail-h99" not in output


def test_useravailsessions_empty():
    assert dv_filters.useravailsessions(None, USER) == ""
    assert dv_filters.useravailsessions_readonly({}, USER) == ""


@pytest.mark.parametrize(
    "availability,css,icon",
    [("i", "warning", "ok-circle"), ("n", "danger", "remove-sign")],
)
def test_readonly_availability_states(availability, css, icon):
    output = dv_filters.useravailsessions_readonly(
        {key(AVAILABILITY_FIELDKEY): availability}, USER
    )

    assert f'class="{css}"' in output
    assert f"glyphicon-{icon}" in output


def test_readonly_skips_other_sessions_when_sesskey_given():
    struct = {
        key(AVAILABILITY_FIELDKEY): "y",
        key(AVAILABILITY_FIELDKEY, spk=43): "y",
    }

    output = dv_filters.useravailsessions_readonly(struct, USER, sesskey=43)

    assert output.count("<td") == 1
    assert 'data-test="avail-h7-s43"' in output


@pytest.mark.parametrize(
    "chosen,expected",
    [
        (CHOSEN_AS_LEADER, "-->M2</div>"),
        (CHOSEN_AS_HELPER, "-->M1</div>"),
        (CHOSEN_AS_ACTOR, "glyphicon-sunglasses"),
        (CHOSEN_AS_REPLACEMENT, "-->S</div>"),
        (CHOSEN_AS_LEGACY, "glyphicon-check"),
        (CHOSEN_AS_NOT, "glyphicon-unchecked"),
    ],
)
def test_readonly_staff_choice(chosen, expected):
    struct = {key(AVAILABILITY_FIELDKEY): "y", key(STAFF_FIELDKEY): chosen}

    output = dv_filters.useravailsessions_readonly(struct, USER)

    assert expected in output


def test_planning_not_chosen_is_danger():
    struct = {key(AVAILABILITY_FIELDKEY): "y", key(STAFF_FIELDKEY): CHOSEN_AS_NOT}

    output = dv_filters.userplanning_sessions_readonly(struct, USER)

    assert 'class="danger"' in output
    assert "glyphicon-remove-sign" in output


def test_planning_unavailable_and_superleader():
    struct = {
        key(AVAILABILITY_FIELDKEY): "n",
        key(SUPERLEADER_FIELDKEY): True,
    }

    output = dv_filters.userplanning_sessions_readonly(struct, USER)

    assert 'class="danger"' in output
    assert "glyphicon-remove-sign" in output
    assert "&nbsp;/&nbsp;" in output
    assert "M+" in output


def test_readonly_locked_choice_is_info():
    struct = {key(AVAILABILITY_FIELDKEY): "y", key(CHOICE_FIELDKEY): True}

    output = dv_filters.useravailsessions_readonly(struct, USER)

    assert 'class="info"' in output


def test_readonly_conflict_link():
    session = SimpleNamespace(pk=99, season=SimpleNamespace(pk=5))
    struct = {
        key(AVAILABILITY_FIELDKEY): "y",
        key(CONFLICT_FIELDKEY): [SimpleNamespace(session=session)],
    }

    with override("fr"):
        output = dv_filters.useravailsessions_readonly(struct, USER)

    assert 'class="text-danger"' in output
    assert "#sess99" in output
    assert "glyphicon-alert" in output


def test_readonly_onlyavail_blanks_unavailable():
    struct = {key(AVAILABILITY_FIELDKEY): "n"}

    output = dv_filters.useravailsessions_readonly(struct, USER, onlyavail=True)

    assert "--> </div>" in output


def test_userstaffsessions_renders_widget_per_session():
    staffkey = key(STAFF_FIELDKEY)
    form = AvailForm([staffkey], initial={key(AVAILABILITY_FIELDKEY): "y"})

    output = dv_filters.userstaffsessions(form, USER)

    assert f'id="{staffkey}"' in output
    assert output.count("<td") == 1


def test_userstaffsessions_empty():
    assert dv_filters.userstaffsessions(None, USER) == ""


def test_chosen_staff_for_season():
    struct = {
        key(AVAILABILITY_FIELDKEY): "y",
        key(CHOICE_FIELDKEY): True,
        key(STAFF_FIELDKEY): CHOSEN_AS_HELPER,
        key(AVAILABILITY_FIELDKEY, spk=43): "i",
        key(STAFF_FIELDKEY, spk=43): CHOSEN_AS_NOT,
        key(AVAILABILITY_FIELDKEY, spk=44): "n",
    }

    assert dv_filters.chosen_staff_for_season(struct, USER) == 1
    assert dv_filters.chosen_staff_for_season({}, USER) == ""


def test_work_wish_for_season():
    wwkey = SEASON_WORKWISH_FIELDKEY.format(hpk=USER.pk)

    assert dv_filters.work_wish_for_season({wwkey: "3"}, USER) == 3
    assert dv_filters.work_wish_for_season({wwkey: "0"}, USER) == ""
    assert dv_filters.work_wish_for_season({"other": 1}, USER) == ""
    assert dv_filters.work_wish_for_season(None, USER) == ""


def test_weeknumber():
    assert dv_filters.weeknumber(None) == ""
    assert dv_filters.weeknumber(datetime.date(2024, 1, 8)) == "02"


def test_date_ch_short():
    day = datetime.date(2024, 3, 5)

    assert dv_filters.date_ch_short(None) == ""
    with override("de"):
        assert dv_filters.date_ch_short(day) == "5. März"
    with override("fr"):
        assert dv_filters.date_ch_short(day) == "5 mars"


def test_cantons_abbr_without_abbr():
    with override("fr"):
        assert dv_filters.cantons_abbr(["GE"], abbr=False) == ["Genève"]


def test_canton_abbr_unknown_returns_value():
    assert dv_filters.canton_abbr("XX") == "XX"
    assert dv_filters.canton_abbr_short("XX") == "XX"
    assert dv_filters.ifcanton_abbr("XX") == "XX"


def test_canton_abbr_short_known():
    assert dv_filters.canton_abbr_short("VD").startswith('<abbr title="')
    assert dv_filters.ifcanton_abbr("VD").endswith(">VD</abbr>")


def test_season_verb():
    with override("fr"):
        assert dv_filters.season_verb(DV_SEASON_SPRING) == "Printemps"
    assert dv_filters.season_verb(999) == ""


def test_season_month_start_and_end():
    with override("fr"):
        assert dv_filters.season_month_start(DV_SEASON_SPRING) == "janvier"
        assert dv_filters.season_month_start(DV_SEASON_AUTUMN) == "août"
        assert dv_filters.season_month_end(DV_SEASON_SPRING) == "juillet"
        assert dv_filters.season_month_end(DV_SEASON_AUTUMN) == "décembre"
    assert dv_filters.season_month_start(999) == ""
    assert dv_filters.season_month_end(999) == ""


def test_dv_season():
    assert dv_filters.dv_season(datetime.date(2023, 3, 1)) == {
        "year": 2023,
        "dv_season": DV_SEASON_SPRING,
    }
    assert dv_filters.dv_season(datetime.date(2023, 10, 1))["dv_season"] == (
        DV_SEASON_AUTUMN
    )


def test_anyofusercantons():
    with patch.object(dv_filters, "user_cantons", return_value=["VD", "GE"]):
        assert sorted(dv_filters.anyofusercantons(USER, ["GE", "NE"])) == ["GE"]


def test_anyofusercantons_permission_denied():
    with patch.object(dv_filters, "user_cantons", side_effect=PermissionDenied):
        assert dv_filters.anyofusercantons(USER, ["GE"]) is None


@pytest.mark.xfail(
    reason="user_cantons raises LookupError but anyofusercantons only catches "
    "PermissionDenied (defivelo/templatetags/dv_filters.py:520)",
    raises=LookupError,
    strict=True,
)
def test_anyofusercantons_without_cantons():
    with patch.object(dv_filters, "user_cantons", side_effect=LookupError):
        assert dv_filters.anyofusercantons(USER, ["GE"]) is None


def test_inusercantons():
    with (
        patch.object(dv_filters, "has_permission", return_value=False),
        patch.object(dv_filters, "user_cantons", return_value=["VD"]),
    ):
        assert dv_filters.inusercantons(USER, "VD") is True
        assert dv_filters.inusercantons(USER, "GE") is False

    with (
        patch.object(dv_filters, "has_permission", return_value=False),
        patch.object(dv_filters, "user_cantons", side_effect=LookupError),
    ):
        assert dv_filters.inusercantons(USER, "VD") is False

    with patch.object(dv_filters, "has_permission", return_value=True):
        assert dv_filters.inusercantons(USER, "") is True


@pytest.mark.django_db
def test_unprivileged_user_can_see():
    coordinator = UserFactory()
    orga = OrganizationFactory(address_canton="VD", coordinator=coordinator)
    season = SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["VD"])
    QualificationFactory(
        session=SessionFactory(orga=orga, day=datetime.date(2030, 3, 4))
    )

    assert dv_filters.unprivileged_user_can_see(coordinator, season) is True
    assert dv_filters.unprivileged_user_can_see(UserFactory(), season) is False


def test_lettercounter():
    assert dv_filters.lettercounter("1") == "A"
    assert dv_filters.lettercounter(26) == "Z"
    assert dv_filters.lettercounter(27) == 27


def test_canton_colors():
    assert set(dv_filters.canton_colors()) >= set(DV_STATES)


def test_add_qs():
    assert dv_filters.add_qs("/fr/user/", page=2) == "/fr/user/?page=2"


@pytest.mark.xfail(
    reason="remove_qs/add_qs parse `parsed_url.params` instead of `.query`, so "
    "existing querystrings are dropped (defivelo/templatetags/dv_filters.py:561,576)",
    strict=True,
)
def test_add_qs_keeps_existing_querystring():
    assert dv_filters.add_qs("/fr/user/?a=1", page=2) == "/fr/user/?a=1&page=2"


@pytest.mark.xfail(
    reason="remove_qs/add_qs parse `parsed_url.params` instead of `.query`, so "
    "existing querystrings are dropped (defivelo/templatetags/dv_filters.py:561,576)",
    strict=True,
)
def test_remove_qs_keeps_other_params():
    assert dv_filters.remove_qs("/fr/user/?a=1&page=2", "page") == "/fr/user/?a=1"


def test_get_timesheet_status_for_canton():
    mcv = SimpleNamespace(canton="VD")

    assert dv_filters.get_timesheet_status_for_canton(mcv, {"VD": "ok"}) == "ok"
    assert dv_filters.get_timesheet_status_for_canton(mcv, {}) is None


def test_vcs_tags(settings):
    settings.VCS_VERSION = "1.2.3"
    settings.VCS_COMMIT = "abcdef"

    assert dv_filters.vcs_version() == "1.2.3"
    assert dv_filters.vcs_commit() == "abcdef"


def test_setlang():
    request = SimpleNamespace(LANGUAGE_CODE="fr", path="/fr/user/")

    assert dv_filters.setlang(request, "de") == "/de/user/"
