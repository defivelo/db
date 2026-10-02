import importlib
import os
from datetime import date
from unittest.mock import patch

from django.test import override_settings
from django.urls import clear_url_caches

from apps.common import DV_SEASON_AUTUMN, DV_SEASON_SPRING
from defivelo import get_project_root_path, import_env_vars
from defivelo.views import common


def test_import_env_vars_sets_missing_variables(tmp_path, monkeypatch):
    monkeypatch.delenv("DV_TEST_NEW_VAR", raising=False)
    monkeypatch.setenv("DV_TEST_EXISTING_VAR", "kept")
    (tmp_path / "DV_TEST_NEW_VAR").write_text("  value\n")
    (tmp_path / "DV_TEST_EXISTING_VAR").write_text("overwritten")
    (tmp_path / "subdir").mkdir()

    try:
        import_env_vars(str(tmp_path))

        assert os.environ["DV_TEST_NEW_VAR"] == "value"
        assert os.environ["DV_TEST_EXISTING_VAR"] == "kept"
        assert "subdir" not in os.environ
    finally:
        os.environ.pop("DV_TEST_NEW_VAR", None)


def test_get_project_root_path():
    assert os.path.isfile(os.path.join(get_project_root_path(), "manage.py"))


def test_urls_include_debug_toolbar_when_debug():
    import defivelo.urls as urls

    try:
        with override_settings(DEBUG=True):
            importlib.reload(urls)
            patterns = [str(p.pattern) for p in urls.urlpatterns]
        assert patterns[0] == "^__debug__/"
    finally:
        importlib.reload(urls)
        clear_url_caches()

    assert "^__debug__/" not in [str(p.pattern) for p in urls.urlpatterns]


def test_menu_view_current_season():
    class FakeDate(date):
        current = date(2024, 3, 1)

        @classmethod
        def today(cls):
            return cls.current

    with patch.object(common, "date", FakeDate):
        assert common.MenuView().current_season() == DV_SEASON_SPRING
        FakeDate.current = date(2024, 10, 1)
        assert common.MenuView().current_season() == DV_SEASON_AUTUMN
