from unittest import mock

from django.conf import settings
from django.core import mail
from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation

from .models import ContactMessage, ProcessStep, Project, Reference, Service, SiteSettings


class PagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(
            title="Test Kule", slug="test-kule", summary="özet",
            category=Project.Category.RESIDENTIAL, is_featured=True,
        )
        Service.objects.create(title="Hizmet", slug="hizmet", summary="özet")

    def test_every_page_loads(self):
        for name, kwargs in [
            ("main:home", {}),
            ("main:project_list", {}),
            ("main:service_list", {}),
            ("main:about", {}),
            ("main:contact", {}),
            ("main:project_detail", {"slug": self.project.slug}),
        ]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, kwargs=kwargs)).status_code, 200)

    def test_unknown_project_is_404(self):
        self.assertEqual(self.client.get("/projects/nope/").status_code, 404)


class ProjectFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Project.objects.create(title="A", slug="a", summary="s",
                               category=Project.Category.RESIDENTIAL)
        Project.objects.create(title="B", slug="b", summary="s",
                               category=Project.Category.INDUSTRIAL)

    def test_valid_category_filters(self):
        response = self.client.get(reverse("main:project_list"), {"category": "industrial"})
        self.assertEqual([p.title for p in response.context["projects"]], ["B"])

    def test_unknown_category_is_ignored_not_applied(self):
        # A bogus value must fall through to "show everything", never reach the ORM.
        response = self.client.get(reverse("main:project_list"), {"category": "bogus"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["projects"].count(), 2)


class ContactFormTests(TestCase):
    def test_valid_submission_saves_and_redirects(self):
        response = self.client.post(reverse("main:contact"), {
            "name": "Mehmet Yılmaz", "phone": "05321234567",
            "email": "m@example.com", "subject": "Teklif",
            "message": "Danışmanlık talebim var.",
        })
        self.assertRedirects(response, reverse("main:contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_persian_digits_are_normalised_to_ascii(self):
        self.client.post(reverse("main:contact"), {
            "name": "Ali", "phone": "۰۵۳۲۱۲۳۴۵۶۷", "message": "Merhaba",
        })
        self.assertEqual(ContactMessage.objects.get().phone, "05321234567")

    def test_short_phone_is_rejected(self):
        response = self.client.post(reverse("main:contact"), {
            "name": "x", "phone": "12", "message": "y",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("phone", response.context["form"].errors)
        self.assertFalse(ContactMessage.objects.exists())


class HeroVariantTests(TestCase):
    """The hero branches server-side: uploaded photo, else the procedural tower."""

    GIF = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02D\x01\x00;"
    )

    def test_tower_is_used_when_no_photo_uploaded(self):
        site = SiteSettings.load()
        site.hero_image = ""
        site.save()
        html = self.client.get(reverse("main:home")).content.decode()
        self.assertIn('id="hero-canvas"', html)
        self.assertNotIn('id="hero-photo"', html)

    def test_photo_is_used_when_uploaded(self):
        site = SiteSettings.load()
        # A 1x1 GIF is enough: the template only needs the field to be set.
        site.hero_image.save("t.gif", ContentFile(self.GIF), save=True)
        self.addCleanup(site.hero_image.delete, save=True)

        html = self.client.get(reverse("main:home")).content.decode()
        self.assertIn('id="hero-photo"', html)
        self.assertIn(site.hero_image.url, html)
        self.assertNotIn('id="hero-canvas"', html)

    def test_photo_hero_does_not_ship_threejs(self):
        """The photo path has no 3D, so it must not pay the three.js download."""
        site = SiteSettings.load()
        site.hero_image.save("t.gif", ContentFile(self.GIF), save=True)
        self.addCleanup(site.hero_image.delete, save=True)

        self.assertNotIn('import("three")', self.client.get(reverse("main:home")).content.decode())

    def test_tower_hero_does_ship_threejs(self):
        site = SiteSettings.load()
        site.hero_image = ""
        site.save()
        self.assertIn('import("three")', self.client.get(reverse("main:home")).content.decode())


class RevealSectionTests(TestCase):
    """Scroll-reveal images prefer real project covers, else the hero image."""

    GIF = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02D\x01\x00;"
    )

    def test_featured_covers_are_used_and_shapes_alternate(self):
        for i in range(2):
            p = Project.objects.create(
                title=f"P{i}", slug=f"p{i}", summary="s", is_featured=True, order=i
            )
            p.cover.save(f"c{i}.gif", ContentFile(self.GIF), save=True)
            self.addCleanup(p.cover.delete, save=False)

        reveals = self.client.get(reverse("main:home")).context["reveals"]
        self.assertEqual([r["title"] for r in reveals], ["P0", "P1"])
        self.assertEqual([r["shape"] for r in reveals], ["circle", "rounded"])

    def test_falls_back_to_hero_image_when_no_covers(self):
        site = SiteSettings.load()
        site.hero_image.save("h.gif", ContentFile(self.GIF), save=True)
        self.addCleanup(site.hero_image.delete, save=True)

        reveals = self.client.get(reverse("main:home")).context["reveals"]
        self.assertEqual(len(reveals), 1)
        self.assertEqual(reveals[0]["src"], site.hero_image.url)

    def test_section_is_omitted_entirely_when_there_is_nothing_to_show(self):
        site = SiteSettings.load()
        site.hero_image = ""
        site.save()
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.context["reveals"], [])
        # Match the rendered card, not the class name — that also appears in the
        # page's JavaScript selector, which ships whether or not a card renders.
        self.assertNotIn('class="reveal-mask ', response.content.decode())


class TemplateHygieneTests(SimpleTestCase):
    def test_no_multiline_hash_comments(self):
        """`{# … #}` is single-line only in Django.

        Spread one over two lines and it is not parsed as a comment at all — the
        text renders on the page. Use `{% comment %}` for anything multi-line.
        """
        offenders = []
        for root in (settings.BASE_DIR / "templates", settings.BASE_DIR / "main" / "templates"):
            for path in root.rglob("*.html"):
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if "{#" in line and "#}" not in line:
                        rel = path.relative_to(settings.BASE_DIR)
                        offenders.append(f"{rel}:{lineno}: {line.strip()[:60]}")

        self.assertEqual(offenders, [], "Multi-line {# #} renders as visible text:\n" + "\n".join(offenders))


class SiteSettingsTests(TestCase):
    def test_stays_a_singleton(self):
        SiteSettings.objects.create(company_name="Birinci")
        SiteSettings.objects.create(company_name="İkinci")
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.load().company_name, "İkinci")

    def test_load_creates_the_row_when_missing(self):
        SiteSettings.objects.all().delete()
        self.assertIsNotNone(SiteSettings.load().pk)


class NewSectionsTests(TestCase):
    """Process timeline, references and the before/after comparison."""

    GIF = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02D\x01\x00;"
    )

    def test_sections_are_omitted_when_empty(self):
        response = self.client.get(reverse("main:home"))
        self.assertEqual(list(response.context["steps"]), [])
        self.assertIsNone(response.context["comparison"])
        # Match the rendered figure, not the attribute — that also appears in
        # the page's JavaScript selector, which ships either way.
        self.assertNotIn('<figure class="ba"', response.content.decode())

    def test_process_steps_render_in_order(self):
        for i, title in enumerate(["Keşif", "Tasarım", "Uygulama"]):
            ProcessStep.objects.create(title=title, description="d", order=i)
        html = self.client.get(reverse("main:home")).content.decode()
        self.assertLess(html.index("Keşif"), html.index("Tasarım"))
        self.assertLess(html.index("Tasarım"), html.index("Uygulama"))

    def test_references_split_by_kind(self):
        Reference.objects.create(name="Acme", kind=Reference.Kind.CLIENT)
        Reference.objects.create(name="ISO 9001", kind=Reference.Kind.CERTIFICATE)
        ctx = self.client.get(reverse("main:home")).context
        self.assertEqual([r.name for r in ctx["clients"]], ["Acme"])
        self.assertEqual([r.name for r in ctx["certificates"]], ["ISO 9001"])

    def test_comparison_needs_both_images(self):
        p = Project.objects.create(title="R", slug="r", summary="s")
        p.before_image.save("b.gif", ContentFile(self.GIF), save=True)
        self.addCleanup(p.before_image.delete, save=False)
        # Only one of the pair — the slider must stay hidden.
        self.assertIsNone(self.client.get(reverse("main:home")).context["comparison"])
        self.assertFalse(p.has_comparison)

        p.after_image.save("a.gif", ContentFile(self.GIF), save=True)
        self.addCleanup(p.after_image.delete, save=False)
        self.assertTrue(Project.objects.get(pk=p.pk).has_comparison)
        self.assertIsNotNone(self.client.get(reverse("main:home")).context["comparison"])


class TranslationTests(TestCase):
    def test_english_url_serves_english_ui(self):
        html = self.client.get("/en/").content.decode()
        self.assertIn('lang="en"', html)
        self.assertIn("Projects", html)

    def test_turkish_stays_unprefixed(self):
        html = self.client.get("/").content.decode()
        self.assertIn('lang="tr"', html)
        self.assertIn("Projeler", html)

    def test_model_falls_back_to_turkish_when_no_translation(self):
        s = Service.objects.create(title="Konut", slug="k", summary="özet")
        with translation.override("en"):
            self.assertEqual(s.t("title"), "Konut")     # no title_en set
            s.title_en = "Housing"
            self.assertEqual(s.t("title"), "Housing")
        with translation.override("tr"):
            self.assertEqual(s.t("title"), "Konut")


class SeoTests(TestCase):
    def test_sitemap_lists_projects(self):
        Project.objects.create(title="P", slug="p-seo", summary="s")
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
        self.assertIn("p-seo", body)

    def test_robots_txt_is_served_as_plain_text(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "text/plain")
        self.assertIn("Sitemap:", r.content.decode())

    def test_home_carries_open_graph_and_structured_data(self):
        html = self.client.get(reverse("main:home")).content.decode()
        self.assertIn('property="og:title"', html)
        self.assertIn('rel="canonical"', html)
        self.assertIn('hreflang="en"', html)
        self.assertIn("GeneralContractor", html)


class WhatsAppTests(TestCase):
    def test_button_hidden_until_a_number_is_set(self):
        site = SiteSettings.load()
        site.whatsapp = ""
        site.save()
        self.assertNotIn("wa.me", self.client.get(reverse("main:home")).content.decode())

    def test_button_links_to_the_number(self):
        site = SiteSettings.load()
        site.whatsapp = "905321234567"
        site.save()
        self.assertIn("wa.me/905321234567", self.client.get(reverse("main:home")).content.decode())


class ContactNotifyTests(TestCase):
    def test_email_sent_when_notify_address_set(self):
        site = SiteSettings.load()
        site.notify_email = "office@example.com"
        site.save()
        self.client.post(reverse("main:contact"), {
            "name": "Ali", "phone": "05321234567", "message": "Merhaba",
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Ali", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["office@example.com"])

    def test_no_email_when_address_blank(self):
        site = SiteSettings.load()
        site.notify_email = ""
        site.save()
        self.client.post(reverse("main:contact"), {
            "name": "Ali", "phone": "05321234567", "message": "Merhaba",
        })
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ContactMessage.objects.count(), 1)  # still saved

    def test_mail_failure_does_not_break_the_submission(self):
        """A mail outage must not turn a saved enquiry into a 500."""
        site = SiteSettings.load()
        site.notify_email = "office@example.com"
        site.save()
        with mock.patch("main.views.send_mail", side_effect=OSError("smtp down")):
            with self.assertLogs("main.views", level="ERROR"):
                response = self.client.post(reverse("main:contact"), {
                    "name": "Ali", "phone": "05321234567", "message": "Merhaba",
                })
        self.assertRedirects(response, reverse("main:contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)
