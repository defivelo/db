# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from localflavor.ch.ch_states import STATE_CHOICES

from django.utils.translation import ugettext_lazy as _

STATE_CHOICES_WITH_DEFAULT = tuple(
    list((('', '---------',),)) +
    list(STATE_CHOICES)
)