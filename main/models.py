from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language


class Translatable:
    """Picks the `_en` variant of a field when English is active.

    Content lives in the database, so `{% trans %}` can't reach it — each
    translatable field has an optional `<name>_en` sibling. Falling back to the
    Turkish value means a half-translated record still renders rather than
    showing blanks.
    """

    def t(self, field):
        if (get_language() or "").startswith("en"):
            return getattr(self, f"{field}_en", "") or getattr(self, field)
        return getattr(self, field)


class SiteSettings(Translatable, models.Model):
    """Singleton row holding the company details shown in header/footer."""

    company_name = models.CharField("Şirket adı", max_length=120, default="REN")
    tagline = models.CharField("Slogan", max_length=200, blank=True)
    tagline_en = models.CharField("Slogan (EN)", max_length=200, blank=True)
    about = models.TextField("Hakkımızda", blank=True)
    about_en = models.TextField("Hakkımızda (EN)", blank=True)

    hero_image = models.ImageField(
        "Ana sayfa görseli",
        upload_to="hero/",
        blank=True,
        help_text=(
            "Ana sayfanın arka plan görseli. Kaydırdıkça görselin üstünden altına "
            "doğru hareket eder, bu yüzden dikey ve uzun fotoğraflar en iyi sonucu "
            "verir. Boş bırakılırsa görsel yerine 3B bir kule gösterilir."
        ),
    )

    phone = models.CharField("Telefon", max_length=40, blank=True)
    email = models.EmailField("E-posta", blank=True)
    address = models.CharField("Adres", max_length=300, blank=True)
    whatsapp = models.CharField(
        "WhatsApp numarası",
        max_length=40,
        blank=True,
        help_text="Ülke kodu ile, ör. 905321234567. Boşsa buton gösterilmez.",
    )
    notify_email = models.EmailField(
        "Bildirim e-postası",
        blank=True,
        help_text="İletişim formu mesajları buraya iletilir. Boşsa yalnızca panele düşer.",
    )

    instagram = models.URLField("Instagram", blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)

    years_experience = models.PositiveIntegerField("Yıl deneyim", default=0)
    projects_done = models.PositiveIntegerField("Tamamlanan proje", default=0)
    area_built = models.PositiveIntegerField("İnşa edilen alan", default=0)

    class Meta:
        verbose_name = "Site ayarları"
        verbose_name_plural = "Site ayarları"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # Force a single row: always write to pk=1 no matter how it was created.
        # Dropping force_insert lets a second `objects.create()` update the existing
        # row instead of raising IntegrityError on the duplicate pk.
        self.pk = 1
        kwargs.pop("force_insert", None)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # the site templates always expect this row to exist

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Service(Translatable, models.Model):
    """One offering — 'Konut inşaatı', 'Renovasyon', etc."""

    title_en = models.CharField("Başlık (EN)", max_length=120, blank=True)
    summary_en = models.CharField("Özet (EN)", max_length=300, blank=True)
    title = models.CharField("Başlık", max_length=120)
    slug = models.SlugField("Kısa ad", max_length=140, unique=True, allow_unicode=True)
    summary = models.CharField("Özet", max_length=300)
    description = models.TextField("Açıklama", blank=True)
    # Name of an inline SVG block in templates, e.g. "building" — not an emoji.
    icon = models.CharField(
        "Simge",
        max_length=40,
        default="building",
        help_text="Şunlardan biri: building, crane, ruler, wrench, hardhat, leaf",
    )
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Hizmet"
        verbose_name_plural = "Hizmetler"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Project(Translatable, models.Model):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Tamamlandı"
        ONGOING = "ongoing", "Devam ediyor"
        PLANNED = "planned", "Tasarım aşamasında"

    class Category(models.TextChoices):
        RESIDENTIAL = "residential", "Konut"
        COMMERCIAL = "commercial", "Ticari"
        INDUSTRIAL = "industrial", "Endüstriyel"
        RENOVATION = "renovation", "Renovasyon"

    title = models.CharField("Başlık", max_length=160)
    title_en = models.CharField("Başlık (EN)", max_length=160, blank=True)
    slug = models.SlugField("Kısa ad", max_length=180, unique=True, allow_unicode=True)
    category = models.CharField(
        "Kategori", max_length=20, choices=Category.choices, default=Category.RESIDENTIAL
    )
    status = models.CharField(
        "Durum", max_length=20, choices=Status.choices, default=Status.COMPLETED
    )

    summary = models.CharField("Özet", max_length=300)
    summary_en = models.CharField("Özet (EN)", max_length=300, blank=True)
    description = models.TextField("Proje açıklaması", blank=True)
    description_en = models.TextField("Proje açıklaması (EN)", blank=True)

    location = models.CharField("Konum", max_length=160, blank=True)
    client = models.CharField("İşveren", max_length=160, blank=True)
    area_m2 = models.PositiveIntegerField(
        "Alan (m²)", null=True, blank=True, validators=[MinValueValidator(1)]
    )
    year = models.PositiveIntegerField("Yıl", null=True, blank=True)

    cover = models.ImageField("Kapak görseli", upload_to="projects/", blank=True)

    # Both must be set for the drag-to-compare slider to appear.
    before_image = models.ImageField("Öncesi görseli", upload_to="projects/ba/", blank=True)
    after_image = models.ImageField("Sonrası görseli", upload_to="projects/ba/", blank=True)
    is_featured = models.BooleanField("Ana sayfada göster", default=False)
    order = models.PositiveIntegerField("Sıra", default=0)
    created_at = models.DateTimeField("Kayıt tarihi", auto_now_add=True)

    class Meta:
        verbose_name = "Proje"
        verbose_name_plural = "Projeler"
        ordering = ["order", "-year", "-id"]
        indexes = [models.Index(fields=["is_featured", "order"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("main:project_detail", kwargs={"slug": self.slug})

    @property
    def has_comparison(self):
        return bool(self.before_image and self.after_image)


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="images", verbose_name="Proje"
    )
    image = models.ImageField("Görsel", upload_to="projects/gallery/")
    caption = models.CharField("Açıklama", max_length=200, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        verbose_name = "Proje görseli"
        verbose_name_plural = "Proje görselleri"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.caption or self.pk}"


class ContactMessage(models.Model):
    name = models.CharField("Ad Soyad", max_length=120)
    phone = models.CharField("Telefon", max_length=40)
    email = models.EmailField("E-posta", blank=True)
    subject = models.CharField("Konu", max_length=200, blank=True)
    message = models.TextField("Mesaj")
    created_at = models.DateTimeField("Gönderim tarihi", auto_now_add=True)
    is_read = models.BooleanField("Okundu", default=False)

    class Meta:
        verbose_name = "İletişim mesajı"
        verbose_name_plural = "İletişim mesajları"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.subject or 'Konusuz'}"


class ProcessStep(Translatable, models.Model):
    """One stage of "how we work" — rendered as a numbered timeline."""

    title = models.CharField("Başlık", max_length=120)
    title_en = models.CharField("Başlık (EN)", max_length=120, blank=True)
    description = models.CharField("Açıklama", max_length=300)
    description_en = models.CharField("Açıklama (EN)", max_length=300, blank=True)
    duration = models.CharField(
        "Süre", max_length=60, blank=True, help_text="ör. 2-4 hafta"
    )
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        verbose_name = "Süreç adımı"
        verbose_name_plural = "Süreç adımları"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Reference(models.Model):
    """A client logo or a certificate — trust signals, not decoration."""

    class Kind(models.TextChoices):
        CLIENT = "client", "İşveren"
        CERTIFICATE = "certificate", "Sertifika"

    name = models.CharField("Ad", max_length=140)
    kind = models.CharField("Tür", max_length=20, choices=Kind.choices, default=Kind.CLIENT)
    logo = models.ImageField("Logo", upload_to="references/", blank=True)
    url = models.URLField("Bağlantı", blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        verbose_name = "Referans"
        verbose_name_plural = "Referanslar"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name
