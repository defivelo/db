from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "apps.user"
    verbose_name = "Users"

    def ready(self) -> None:  # type: ignore[override]
        # Import signal handlers to ensure they are registered at startup
        from . import signals  # noqa: F401

        return super().ready()
