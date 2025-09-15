# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016, 2020 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime

from django.test import TestCase
from django.urls import reverse

from defivelo.tests.utils import StateManagerAuthClient

from .factories import SeasonFactory, SessionFactory


class SessionCloneViewTest(TestCase):
    def setUp(self):
        self.client = StateManagerAuthClient()
        self.season = SeasonFactory(
            cantons=["VD"], year=2019, month_start=1, n_months=3
        )
        self.session = SessionFactory(
            orga__address_canton="VD",
            day=datetime.date(2019, 2, 11),
            begin=datetime.time(9, 30),
        )
        super().setUp()

    def test_get_session_clone_view(self):
        url = reverse(
            "session-clone", kwargs={"seasonpk": self.season.pk, "pk": self.session.pk}
        )

        post_url = reverse("session-create", kwargs={"seasonpk": self.season.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        context_session = response.context["session"]
        self.assertIsNone(context_session.pk)
        self.assertIsNone(context_session.day)
        self.assertIsNone(context_session.begin)

        self.assertContains(response, 'action="{}"'.format(post_url))

    def test_get_form_kwargs_clears_clone_fields(self):
        url = reverse(
            "session-clone", kwargs={"seasonpk": self.season.pk, "pk": self.session.pk}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        instance = response.context["form"].instance
        self.assertIsNone(instance.pk)
        self.assertIsNone(instance.day)
        self.assertIsNone(instance.begin)

    def test_post_not_allowed_raises_error(self):
        url = reverse(
            "session-clone", kwargs={"seasonpk": self.season.pk, "pk": self.session.pk}
        )

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 403)  # PermissionDenied

    def test_clone_payload_can_create(self):
        url_clone = reverse(
            "session-clone", kwargs={"seasonpk": self.season.pk, "pk": self.session.pk}
        )
        response = self.client.get(url_clone)
        self.assertEqual(response.status_code, 200)

        session = response.context["form"].instance

        data = {
            "orga": session.orga.pk,
            "place": session.place,
            "address_street": session.address_street,
            "address_no": session.address_no,
            "address_zip": session.address_zip,
            "address_city": session.address_city,
            "address_canton": session.address_canton,
            "fallback_plan": "A",
            "visible": "on",
            "superleader": "",
            "bikes_concept": "Keine",
            "bikes_phone": "+41761121232",
            "apples": "im Cargo",
            "helpers_time": "09:10",
            "helpers_place": session.helpers_place,
            "comments": "",
            "day": "2019-03-11",
            "begin": "09:30",
        }

        url = reverse("session-create", kwargs={"seasonpk": self.season.pk})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "/fr/season/{}".format(self.season.pk),
            response.headers.get("location"),
            "Invalid Redirect url",
        )
