# The MIT License (MIT)
#
# Copyright (c) 2015 Ha Pham
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Models originally based on `simple-article==0.2.1`.
"""

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from tinymce.models import HTMLField


class Article(models.Model):
    """
    Simple article model with basic fields
    """

    title = models.CharField(_("Title"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=True, blank=True)
    summary = models.TextField(_("Summary"), null=True, blank=True)
    image = models.ImageField(
        _("Image"), blank=True, null=True, upload_to="articles/%Y/%m/%d"
    )
    modified = models.DateTimeField(_("Modified"), default=timezone.now)
    published = models.BooleanField(default=False)
    body = HTMLField(_("Body"))
    tags = TaggableManager()

    class Meta:
        ordering = ["-modified"]
        verbose_name = "Article"

    def __str__(self):
        return "Article: %s" % self.title

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slug = slugify(self.title)
            counter = 1
            while self.__class__.objects.filter(slug=self.slug).exists():
                self.slug = "{0}-{1}".format(slug, counter)
            counter += 1
        return super().save(*args, **kwargs)
