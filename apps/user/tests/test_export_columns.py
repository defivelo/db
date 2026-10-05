import csv
import io

from django.urls import reverse

import pytest

from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import CollaboratorAuthClient, PowerUserAuthClient

pytestmark = pytest.mark.django_db

COLLABORATOR_COLUMNS = [
    "Prénom",
    "Nom",
    "E-mail",
    "Natel",
    "Statut",
    "Canton d’affiliation",
    "Défi Vélo Mobile",
    "Langue",
    "Formation",
    "Intervenant·e",
]
SENSITIVE_COLUMNS = ["IBAN", "N° AVS", "Date de naissance", "Rue", "Nom de la banque"]


def export_header(client):
    UserFactory(profile__iban="CH9300762011623852957")
    response = client.get(reverse("user-list-export", kwargs={"format": "csv"}))
    assert response.status_code == 200
    return next(csv.reader(io.StringIO(response.content.decode())))


def test_collaborator_export_is_restricted():
    header = export_header(CollaboratorAuthClient())

    assert header == COLLABORATOR_COLUMNS
    assert not set(SENSITIVE_COLUMNS) & set(header)


def test_power_user_export_has_all_columns():
    header = export_header(PowerUserAuthClient())

    assert set(SENSITIVE_COLUMNS) <= set(header)
    assert header[-2:] == ["Niveau d’accès", "Cantons gérés"]
