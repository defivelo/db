from django.urls import reverse

from apps.user.tests.factories import UserFactory
from defivelo.tests.utils import PowerUserAuthClient

from ...user import FORMATION_M1, FORMATION_M2
from .. import CHOSEN_AS_HELPER, CHOSEN_AS_LEADER
from ..models import HelperSessionAvailability
from .factories import (
    QualificationActivityFactory,
    QualificationFactory,
)
from .test_seasons import SeasonTestCaseMixin


class QualifsTestCase(SeasonTestCaseMixin):
    """
    Test the qualification views
    """

    def setUp(self):
        self.client = PowerUserAuthClient()
        super().setUp()

    def test_n_helper_validation(self):
        """
        Test that the number of helpers is validated according to the number of M1/M2 configured via n_helpers
        """
        actor = self.client.user
        actor.profile.formation = FORMATION_M1
        actor.profile.save()

        session1 = self.sessions[0]

        # Create some M1 and M2 users and their availability for session1
        m1s = UserFactory.create_batch(3, profile__formation=FORMATION_M1)
        m2s = UserFactory.create_batch(1, profile__formation=FORMATION_M2)
        for m1 in m1s:
            HelperSessionAvailability.objects.get_or_create(
                session=session1,
                helper=m1,
                availability="y",
                chosen_as=CHOSEN_AS_HELPER,
            )
        for m2 in m2s:
            HelperSessionAvailability.objects.get_or_create(
                session=session1,
                helper=m2,
                availability="y",
                chosen_as=CHOSEN_AS_LEADER,
            )

        QualificationActivityFactory()

        q = QualificationFactory.create(session=session1)

        data = {
            "session": session1.pk,
            "name": "Lisa Johnson",
            "class_teacher_fullname": q.class_teacher_fullname,
            "class_teacher_natel": "",
            "n_participants": "14",
            "n_bikes": "6",
            "n_helmets": "",
            "leader": str(m2s[0].pk),
            "helpers": [str(m.pk) for m in m1s],
            "n_helpers": 1,  # too many helpers for the selected n_helpers
            "activity_A": "",
            "activity_B": "",
            "activity_C": "",
            "actor": "",
            "comments": "",
        }

        response = self.client.post(
            reverse(
                "quali-update",
                kwargs={
                    "pk": q.pk,
                    "seasonpk": self.season.pk,
                    "sessionpk": session1.pk,
                },
            ),
            {**data, "n_helpers": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pas plus de zéro moniteurs 1")

        response = self.client.post(
            reverse(
                "quali-update",
                kwargs={
                    "pk": q.pk,
                    "seasonpk": self.season.pk,
                    "sessionpk": session1.pk,
                },
            ),
            {
                **data,
                "n_helpers": "3",
                "helpers": [str(m.pk) for m in m1s[0:-1]],
            },
        )
        self.assertEqual(response.status_code, 302)
