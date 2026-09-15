from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7
    i18n = True

    def items(self):
        return ["main:home", "main:project_list", "main:service_list", "main:about", "main:contact"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    i18n = True

    def items(self):
        return Project.objects.all()

    def lastmod(self, obj):
        return obj.created_at


SITEMAPS = {"static": StaticSitemap, "projects": ProjectSitemap}
