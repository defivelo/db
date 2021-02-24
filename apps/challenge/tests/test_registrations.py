import datetime

from django.urls import reverse

from rolepermissions.roles import assign_role

from apps.orga.tests.factories import OrganizationFactory
from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import CoordinatorAuthClient, StateManagerAuthClient

from ..forms.registration import RegistrationFormSet
from ..models import Qualification, Session
from ..models.registration import Registration
from .factories import RegistrationFactory
from .test_seasons import SeasonTestCaseMixin


class RegistrationTestCase(SeasonTestCaseMixin):
    def setUp(self):
        self.client = CoordinatorAuthClient()
        super().setUp()

        # Put the sessions for our Coordinator's orga
        for s in self.sessions:
            s.orga.coordinator = self.client.user
            s.orga.save()

        # Specify one Session's moment
        self.sessions[0].day = datetime.date(2021, 1, 10)
        self.sessions[0].begin = "09:00:00"
        self.sessions[0].save()

        # Specify Season moment
        self.season.year = 2021
        self.season.month_start = 1
        self.season.n_months = 3
        self.season.save()

    def test_coordinator_sees_registrations_form(self):
        response = self.client.get(reverse("registration-create"))
        assert response.status_code == 200
        assert isinstance(response.context.get("formset", None), RegistrationFormSet)

    def test_coordinator_can_submit_registrations_in_season(self):
        organization = self.client.user.managed_organizations.first()
        response = self.client.post(
            reverse("registration-create"),
            data={
                "organization": organization.pk,
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "3",
                "form-MIN_NUM_FORMS": "1",
                "form-MAX_NUM_FORMS": "1",
                "form-0-date": "20.01.2021",
                "form-0-day_time": "13:30:00",
                "form-0-classes_amount": "1",
                "form-1-date": "21.01.2021",
                "form-1-day_time": "08:30:00",
                "form-1-classes_amount": "2",
                "form-__prefix__-date": "",
                "form-__prefix__-day_time": "08:30:00",
                "form-__prefix__-classes_amount": "1",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("registration-confirm")

    def test_coordinator_cant_submit_registrations_out_of_season(self):
        organization = self.client.user.managed_organizations.first()
        response = self.client.post(
            reverse("registration-create"),
            data={
                "organization": organization.pk,
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "3",
                "form-MIN_NUM_FORMS": "1",
                "form-MAX_NUM_FORMS": "1",
                "form-0-date": "20.04.2021",
                "form-0-day_time": "13:30:00",
                "form-0-classes_amount": "1",
                "form-1-date": "21.05.2021",
                "form-1-day_time": "08:30:00",
                "form-1-classes_amount": "2",
                "form-__prefix__-date": "",
                "form-__prefix__-day_time": "08:30:00",
                "form-__prefix__-classes_amount": "1",
            },
        )

        assert response.status_code == 200
        assert len(response.context["formset"].errors) == 2

    def test_coordinator_cant_submit_parallel_sessions(self):
        organization = self.client.user.managed_organizations.first()
        response = self.client.post(
            reverse("registration-create"),
            data={
                "organization": organization.pk,
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "3",
                "form-MIN_NUM_FORMS": "1",
                "form-MAX_NUM_FORMS": "1",
                "form-0-date": "20.02.2021",
                "form-0-day_time": "13:30:00",
                "form-0-classes_amount": "1",
                "form-1-date": "20.02.2021",
                "form-1-day_time": "13:30:00",
                "form-1-classes_amount": "2",
                "form-__prefix__-date": "",
                "form-__prefix__-day_time": "08:30:00",
                "form-__prefix__-classes_amount": "1",
            },
        )

        assert response.status_code == 200
        assert "date" in response.context["formset"].errors[1]

    def test_coordinator_cant_submit_sessions_over_existing_others(self):
        organization = self.client.user.managed_organizations.first()
        response = self.client.post(
            reverse("registration-create"),
            data={
                "organization": organization.pk,
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "1",
                "form-MAX_NUM_FORMS": "1",
                "form-0-date": "10.01.2021",
                "form-0-day_time": "08:30:00",
                "form-0-classes_amount": "1",
                "form-__prefix__-date": "",
                "form-__prefix__-day_time": "08:30:00",
                "form-__prefix__-classes_amount": "1",
            },
        )

        assert response.status_code == 200
        assert len(response.context["formset"].errors) == 1

    def test_coordinator_cant_submit_sessions_to_not_owned_organization(self):
        organization = OrganizationFactory()
        response = self.client.post(
            reverse("registration-create"),
            data={
                "organization": organization.pk,
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "1",
                "form-MAX_NUM_FORMS": "1",
                "form-0-date": "20.01.2021",
                "form-0-day_time": "08:30:00",
                "form-0-classes_amount": "1",
                "form-__prefix__-date": "",
                "form-__prefix__-day_time": "08:30:00",
                "form-__prefix__-classes_amount": "1",
            },
        )

        assert response.status_code == 200
        assert "organization" in response.context["form"].errors

    def test_coordinator_must_accept_conditions(self):
        organization = self.client.user.managed_organizations.first()
        session = self.client.session
        session.update(
            {
                "new_registration": {
                    "organization": organization.pk,
                    "lines": [
                        {
                            "date": "2021-01-20",
                            "day_time": "08:30:00",
                            "classes_amount": 1,
                        }
                    ],
                }
            }
        )
        session.save()
        response = self.client.post(reverse("registration-confirm"), data={})
        assert response.status_code == 200
        assert "is_terms_accepted" in response.context["form"].errors

    def test_coordinator_can_confirm_registrations(self):
        organization = self.client.user.managed_organizations.first()
        http_session = self.client.session
        http_session.update(
            {
                "new_registration": {
                    "organization": organization.pk,
                    "lines": [
                        {
                            "date": "2021-01-20",
                            "day_time": "08:30:00",
                            "classes_amount": 1,
                        }
                    ],
                }
            }
        )
        http_session.save()

        response = self.client.post(
            reverse("registration-confirm"), data={"is_terms_accepted": "on"}
        )
        assert response.status_code == 302

        assert (
            Registration.objects.filter(
                date="2021-01-20",
                day_time="08:30:00",
                classes_amount=1,
                is_archived=False,
                organization_id=organization.id,
            ).count()
            == 1
        )


class RegistrationValidationTestCase(SeasonTestCaseMixin):
    def setUp(self):
        self.client = StateManagerAuthClient()
        super().setUp()

        self.coordinator = UserFactory()
        assign_role(self.coordinator, "coordinator")

        # Put the sessions for our Coordinator's orga
        for s in self.sessions:
            s.orga.coordinator = self.coordinator
            s.orga.save()

        # Specify one Session's moment
        self.sessions[0].day = datetime.date(2021, 1, 10)
        self.sessions[0].begin = "09:00:00"
        self.sessions[0].save()

        # Specify Season moment
        self.season.year = 2021
        self.season.month_start = 1
        self.season.n_months = 3
        self.season.save()

    def test_manager_sees_pending_registrations(self):
        organization = self.sessions[0].orga
        RegistrationFactory(
            date="2021-01-20",
            organization_id=organization.id,
            coordinator_id=organization.coordinator_id,
            day_time="08:30:00",
            classes_amount=1,
        )

        response = self.client.get(reverse("registration-validate"))
        assert response.status_code == 200
        assert str(organization) in response.rendered_content
        assert "20.01.2021" in response.rendered_content

    def test_manager_can_validate_registrations(self):
        organization = self.sessions[0].orga
        registration = RegistrationFactory(
            date="2021-01-20",
            organization_id=organization.id,
            coordinator_id=organization.coordinator_id,
            day_time="08:30:00",
            classes_amount=1,
        )

        response = self.client.post(
            reverse("registration-validate"),
            data={
                "form-organization-id": organization.pk,
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-date": "20.01.2021",
                "form-0-day_time": "08:30:00",
                "form-0-classes_amount": "1",
                "form-0-id": registration.id,
                "form-0-DELETE": "",
                "form-0-is_validated": "true",
            },
        )

        assert response.status_code == 302

        # Will raise DoesNotExist or MultipleObjectsReturned if not ONE session
        # just has been created.
        session = Session.objects.filter(
            orga_id=organization.id, day="2021-01-20", begin="08:30:00"
        ).get()

        assert Qualification.objects.filter(session_id=session.id).count() == 1

    def test_manager_cant_validate_parallel_sessions(self):
        organization = self.sessions[0].orga
        registration1 = RegistrationFactory(
            date="2021-01-20",
            organization_id=organization.id,
            coordinator_id=organization.coordinator_id,
            day_time="08:30:00",
            classes_amount=1,
        )

        registration2 = RegistrationFactory(
            date="2021-01-20",
            organization_id=organization.id,
            coordinator_id=organization.coordinator_id,
            day_time="13:30:00",
            classes_amount=1,
        )

        response = self.client.post(
            reverse("registration-validate"),
            data={
                "form-organization-id": organization.pk,
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-date": "20.01.2021",
                "form-0-day_time": "08:30:00",
                "form-0-classes_amount": "1",
                "form-0-id": registration1.id,
                "form-0-DELETE": "",
                "form-0-is_validated": "true",
                "form-1-date": "20.01.2021",
                "form-1-day_time": "08:30:00",  # Edited to the same moment
                "form-1-classes_amount": "1",
                "form-1-id": registration2.id,
                "form-1-DELETE": "",
                "form-1-is_validated": "true",
            },
        )

        assert response.status_code == 200
        assert not Session.objects.filter(
            orga_id=organization.id, day="2021-01-20", begin="08:30:00"
        ).exists()

    def test_manager_cant_validate_sessions_over_existing(self):
        organization = self.sessions[0].orga
        registration = RegistrationFactory(
            date="2021-01-20",
            organization_id=organization.id,
            coordinator_id=organization.coordinator_id,
            day_time="08:30:00",
            classes_amount=1,
        )

        response = self.client.post(
            reverse("registration-validate"),
            data={
                "form-organization-id": organization.pk,
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-date": "10.01.2021",  # Exists
                "form-0-day_time": "08:30:00",
                "form-0-classes_amount": "1",
                "form-0-id": registration.id,
                "form-0-DELETE": "",
                "form-0-is_validated": "true",
            },
        )

        assert response.status_code == 200
        assert len(response.context["organizations"][0][1].forms[0].errors) == 1
