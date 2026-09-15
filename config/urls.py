from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from main.sitemaps import SITEMAPS

# Not language-prefixed: crawlers and the admin should have stable URLs.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

# Turkish stays at /, English gets /en/ — prefix_default_language=False keeps
# the existing Turkish URLs unchanged so nothing already indexed breaks.
urlpatterns += i18n_patterns(
    path("", include("main.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    # Django serves uploaded media only in development; a real deployment puts
    # MEDIA_ROOT behind the web server instead.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
