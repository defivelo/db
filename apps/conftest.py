import pytest

from apps.challenge.tests.factories import SeasonFactory
from apps.orga.tests.factories import OrganizationFactory
from defivelo.tests.utils import PowerUserAuthClient, StateManagerAuthClient


@pytest.fixture
def orga(db):
    return OrganizationFactory(address_canton="VD")


@pytest.fixture
def season(db):
    return SeasonFactory(year=2030, month_start=1, n_months=6, cantons=["VD"])


@pytest.fixture
def state_manager_client(db):
    return StateManagerAuthClient()


@pytest.fixture
def power_user_client(db):
    return PowerUserAuthClient()
