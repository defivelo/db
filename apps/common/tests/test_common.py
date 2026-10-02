from django.db import models
from django.forms import ChoiceField, Form

import pytest
from tablib import Dataset
from tablib.exceptions import UnsupportedFormat

from apps.common import DV_STATE_CHOICES_WITH_ABBR, format_with_abbr
from apps.common.fields import CheckboxInput, ChoiceArrayField
from apps.common.forms import SelectWithDisabledValues
from apps.common.models import Address
from apps.common.views import ExportMixin


def test_format_with_abbr_with_code():
    assert format_with_abbr("Vaud", "vd") == "Vaud (VD)"


@pytest.mark.parametrize("code", ["", None])
def test_format_with_abbr_without_code(code):
    assert format_with_abbr("Vaud", code) == "Vaud"


def test_state_choices_with_abbr():
    choices = dict(DV_STATE_CHOICES_WITH_ABBR)
    assert str(choices["VD"]) == "Vaud (VD)"


@pytest.mark.parametrize("value", [True, False, None, ""])
def test_checkbox_format_value_empty(value):
    assert CheckboxInput().format_value(value) is None


def test_checkbox_format_value_string():
    assert CheckboxInput().format_value(42) == "42"


def test_checkbox_get_context_checked_and_strips_form_control():
    context = CheckboxInput().get_context("f", True, {"class": "form-control foo"})
    attrs = context["widget"]["attrs"]
    assert attrs["checked"] is True
    assert attrs["class"] == "foo"


@pytest.mark.parametrize(
    "data,expected",
    [({}, False), ({"f": "true"}, True), ({"f": "False"}, False), ({"f": "on"}, True)],
)
def test_checkbox_value_from_datadict(data, expected):
    assert CheckboxInput().value_from_datadict(data, {}, "f") is expected


def test_checkbox_never_omitted():
    assert CheckboxInput().value_omitted_from_data({}, {}, "f") is False


def test_choice_array_field_formfield_uses_checkboxes():
    field = ChoiceArrayField(
        models.CharField(max_length=2, choices=[("a", "A"), ("b", "B")])
    )
    formfield = field.formfield()
    assert list(formfield.choices) == [("a", "A"), ("b", "B")]
    assert formfield.widget.__class__.__name__ == "CheckboxSelectMultiple"


def test_select_disables_none_value():
    widget = SelectWithDisabledValues()
    option = widget.create_option("f", None, "---", False, 0)
    assert option["attrs"]["disabled"] == "disabled"


def test_select_disables_listed_values_unless_selected():
    widget = SelectWithDisabledValues(disabled_values=[2])
    assert widget.create_option("f", 2, "x", False, 0)["attrs"]["disabled"]
    assert "disabled" not in widget.create_option("f", 2, "x", True, 0)["attrs"]
    assert "disabled" not in widget.create_option("f", 3, "x", False, 0)["attrs"]


def test_select_renders_disabled_option():
    class F(Form):
        c = ChoiceField(
            choices=[(1, "un"), (2, "deux")],
            widget=SelectWithDisabledValues(disabled_values=[2]),
        )

    html = str(F()["c"])
    assert '<option value="2" disabled' in html
    assert '<option value="1">' in html


def test_address_canton_full():
    assert Address(address_canton="GE").address_canton_full == "Genève"


class _Request:
    def __init__(self, fmt=None):
        kwargs = {"format": fmt} if fmt else {}
        self.resolver_match = type("RM", (), {"kwargs": kwargs})()


class _DatasetExport(ExportMixin):
    export_filename = "Test"

    def __init__(self, fmt=None):
        self.request = _Request(fmt)

    def get_dataset(self):
        dataset = Dataset(headers=["a", "b"])
        dataset.append([1, 2])
        return dataset


class _Resource:
    def export(self, object_list):
        dataset = Dataset(headers=["x"])
        for obj in object_list:
            dataset.append([obj])
        return dataset


class _ResourceExport(ExportMixin):
    export_class = _Resource()
    export_filename = "Res"

    def __init__(self):
        self.request = _Request("json")
        self.object_list = ["foo", "bar"]


def test_export_mixin_defaults_to_csv():
    response = _DatasetExport().render_to_response({})
    assert response["Content-Type"].startswith("text/csv")
    assert response["Content-Disposition"].startswith('attachment; filename="DV-Test_')
    assert response["Content-Disposition"].endswith('.csv"')
    assert response.content.decode().splitlines() == ["a,b", "1,2"]


def test_export_mixin_uses_export_class():
    response = _ResourceExport().render_to_response({})
    assert response["Content-Type"].startswith("application/json")
    assert response.content == b'[{"x": "foo"}, {"x": "bar"}]'


@pytest.mark.xfail(
    reason="unknown format falls back to CSV metadata but still exports with "
    "the unknown format name",
    raises=UnsupportedFormat,
    strict=True,
)
def test_export_mixin_unknown_format_falls_back_to_csv():
    response = _DatasetExport("foo").render_to_response({})
    assert response["Content-Disposition"].endswith('.csv"')
