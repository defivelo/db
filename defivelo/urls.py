from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'defivelo.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

admin.site.site_header = _('DB Défi Vélo')
