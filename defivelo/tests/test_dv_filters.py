# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
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


from django.test import TestCase
from django.utils.html import escape

from defivelo.templatetags.dv_filters import tel_link


class TelLinkTestCase(TestCase):
    """Tests for the tel_link template filter"""

    def test_empty_string(self):
        """Test that empty string returns empty string"""
        result = tel_link("")
        self.assertEqual(result, "")

    def test_none_value(self):
        """Test that None returns empty string"""
        result = tel_link(None)
        self.assertEqual(result, "")

    def test_swiss_international_format(self):
        """Test Swiss international format +41XXXXXXXXXX"""
        result = tel_link("+41791234567")
        self.assertEqual('<a href="tel:+41791234567">079 123 45 67</a>', result)

    def test_swiss_local_format(self):
        """Test Swiss local format starting with 0"""
        result = tel_link("079 123 45 67")
        self.assertEqual('<a href="tel:+41791234567">079 123 45 67</a>', result)

    def test_swiss_local_format_no_spaces(self):
        """Test Swiss local format without spaces"""
        result = tel_link("0791234567")

        # Should be formatted
        self.assertEqual('<a href="tel:+41791234567">079 123 45 67</a>', result)

    def test_international_non_swiss(self):
        """Test international format for non-Swiss number"""
        # French number
        result = tel_link("+33123456789")

        # Should contain the tel: link with international format
        self.assertIn('href="tel:+33123456789"', result)

        # Should display in national format (without country code)
        self.assertIn("01 23 45 67 89", result)

        # Should be a link
        self.assertIn("<a ", result)
        self.assertIn("</a>", result)

    def test_invalid_phone_number(self):
        """Test invalid phone number returns as-is in display"""
        result = tel_link("invalid")
        self.assertEqual('<a href="tel:invalid">invalid</a>', result)

    def test_invalid_international(self):
        """Test invalid international"""
        result = tel_link("+4179123")
        self.assertEqual('<a href="tel:+4179123">79123</a>', result)

    def test_html_safety(self):
        """Test that the result is marked as safe HTML"""
        result = tel_link("+41791234567")

        # The result should be a SafeString (marked safe)
        from django.utils.safestring import SafeString

        self.assertIsInstance(result, SafeString)

    def test_unsafe_number(self):
        bad_input = "<script>alert('hack')</script>"
        result = tel_link(bad_input)

        # Should escape the link
        self.assertIn(f'href="tel:{escape(bad_input)}"', result)
