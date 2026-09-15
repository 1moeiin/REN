import logging

from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from .forms import ContactForm
from .models import ProcessStep, Project, Reference, Service, SiteSettings

logger = logging.getLogger(__name__)


def _reveal_items(site):
    """Images for the scroll-reveal section, newest featured projects first.

    Falls back to the hero image so the section never renders empty while
    project covers are still being uploaded.
    """
    items = [
        {
            "src": p.cover.url,
            "alt": p.t("title"),
            "title": p.t("title"),
            "caption": p.t("summary"),
            "eyebrow": p.get_category_display(),
            # Alternate the mask so consecutive reveals don't read identically.
            "shape": "circle" if i % 2 == 0 else "rounded",
        }
        for i, p in enumerate(Project.objects.filter(is_featured=True).exclude(cover="")[:3])
    ]

    if not items and site.hero_image:
        items = [{
            "src": site.hero_image.url,
            "alt": site.company_name,
            "title": _("Her proje bir taahhüttür."),
            "caption": _("Bu bölümde işlerinizi görmek için yönetim panelinden projelere kapak görseli yükleyin."),
            "eyebrow": _("Proje"),
            "shape": "circle",
        }]
    return items


def home(request):
    site = SiteSettings.load()
    return render(
        request,
        "main/home.html",
        {
            "services": Service.objects.filter(is_active=True)[:6],
            "projects": Project.objects.filter(is_featured=True)[:6],
            "reveals": _reveal_items(site),
            "steps": ProcessStep.objects.all(),
            "clients": Reference.objects.filter(kind=Reference.Kind.CLIENT),
            "certificates": Reference.objects.filter(kind=Reference.Kind.CERTIFICATE),
            # Raw numbers so the counter can animate up to them; the template
            # renders the formatted value as the no-JS fallback.
            "stats": [
                (site.years_experience, "+", _("yıl deneyim")),
                (site.projects_done, "+", _("tamamlanan proje")),
                (site.area_built, "", _("m² inşa edildi")),
            ],
            "comparison": Project.objects.exclude(before_image="").exclude(after_image="").first(),
        },
    )


def project_list(request):
    projects = Project.objects.all()
    category = request.GET.get("category")
    # Guard against arbitrary ?category= values reaching the ORM as a filter.
    if category in Project.Category.values:
        projects = projects.filter(category=category)
    return render(
        request,
        "main/project_list.html",
        {
            "projects": projects,
            "categories": Project.Category.choices,
            "active_category": category,
        },
    )


def project_detail(request, slug):
    project = get_object_or_404(Project.objects.prefetch_related("images"), slug=slug)
    return render(
        request,
        "main/project_detail.html",
        {
            "project": project,
            "related": Project.objects.filter(category=project.category).exclude(pk=project.pk)[:3],
        },
    )


def service_list(request):
    return render(
        request,
        "main/service_list.html",
        {
            "services": Service.objects.filter(is_active=True),
            "steps": ProcessStep.objects.all(),
        },
    )


def about(request):
    return render(
        request,
        "main/about.html",
        {
            "steps": ProcessStep.objects.all(),
            "clients": Reference.objects.filter(kind=Reference.Kind.CLIENT),
            "certificates": Reference.objects.filter(kind=Reference.Kind.CERTIFICATE),
        },
    )


def _notify(site, msg):
    """Email the new enquiry to the office. Never let this break the response.

    The visitor's message is already saved by the time this runs, so a mail
    outage must not turn a successful submission into a 500.
    """
    if not site.notify_email:
        return
    try:
        send_mail(
            subject=f"[{site.company_name}] {msg.subject or _('Yeni mesaj')} — {msg.name}",
            message=(
                f"{msg.name}\n{msg.phone}\n{msg.email}\n\n{msg.message}\n\n"
                f"— {msg.created_at:%Y-%m-%d %H:%M}"
            ),
            from_email=None,
            recipient_list=[site.notify_email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Contact notification failed for message %s", msg.pk)


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save()
            _notify(SiteSettings.load(), msg)
            messages.success(request, _("Mesajınız alındı. En kısa sürede size dönüş yapacağız."))
            # Redirect after POST so a refresh doesn't resubmit the message.
            return redirect("main:contact")
    else:
        form = ContactForm()
    return render(request, "main/contact.html", {"form": form})


def site_settings(request):
    """Context processor — header and footer need this on every page."""
    return {"site": SiteSettings.load()}
