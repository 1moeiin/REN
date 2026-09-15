from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def switch_language_url(context, lang_code):
    """Current page's URL in another language.

    `translate_url` re-resolves the current path against that language's URL
    patterns, so the switcher lands on the same page rather than the homepage.
    """
    request = context.get("request")
    if not request:
        return "/"
    return translate_url(request.get_full_path(), lang_code)


@register.filter
def t(obj, field):
    """Render a translatable model field: {{ project|t:"title" }}."""
    return obj.t(field) if hasattr(obj, "t") else getattr(obj, field, "")


@register.filter
def webp(field):
    """URL of the `.webp` sibling produced by `manage.py optimize_images`.

    Returns "" when it doesn't exist, so templates can skip the <source> and let
    the browser take the original — the optimiser deliberately omits a WebP
    whenever it would be larger than the source.
    """
    if not field:
        return ""
    from pathlib import Path

    from django.conf import settings

    candidate = Path(settings.MEDIA_ROOT) / Path(field.name).with_suffix(".webp")
    if not candidate.exists():
        return ""
    return settings.MEDIA_URL + str(Path(field.name).with_suffix(".webp")).replace("\\", "/")
