from django.contrib import admin

from .models import (
    ContactMessage,
    ProcessStep,
    Project,
    ProjectImage,
    Reference,
    Service,
    SiteSettings,
)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("image", "caption", "order")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "location", "year", "is_featured", "order")
    list_filter = ("category", "status", "is_featured", "year")
    list_editable = ("is_featured", "order")
    search_fields = ("title", "summary", "location", "client")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProjectImageInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "description")}),
        ("English", {"classes": ("collapse",),
                     "fields": ("title_en", "summary_en", "description_en")}),
        ("Sınıflandırma", {"fields": ("category", "status")}),
        ("Özellikler", {"fields": ("location", "client", "area_m2", "year")}),
        ("Görünüm", {"fields": ("cover", "is_featured", "order")}),
        ("Öncesi / Sonrası", {
            "fields": ("before_image", "after_image"),
            "description": "Her ikisi de yüklenirse projede sürüklenebilir karşılaştırma gösterilir.",
        }),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "description", "icon", "order", "is_active")}),
        ("English", {"classes": ("collapse",), "fields": ("title_en", "summary_en")}),
    )


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "duration")
    ordering = ("order",)
    fieldsets = (
        (None, {"fields": ("title", "description", "duration", "order")}),
        ("English", {"classes": ("collapse",), "fields": ("title_en", "description_en")}),
    )


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "order")
    list_filter = ("kind",)
    list_editable = ("order",)
    search_fields = ("name",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "subject", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "phone", "email", "subject", "message")
    readonly_fields = ("name", "phone", "email", "subject", "message", "created_at")
    actions = ["mark_read", "mark_unread"]

    def has_add_permission(self, request):
        return False  # these only arrive through the public contact form

    @admin.action(description="Okundu olarak işaretle")
    def mark_read(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_read=True)} mesaj okundu olarak işaretlendi.")

    @admin.action(description="Okunmadı olarak işaretle")
    def mark_unread(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_read=False)} mesaj okunmadı olarak işaretlendi.")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Kimlik", {"fields": ("company_name", "tagline", "about", "hero_image")}),
        ("English", {"classes": ("collapse",), "fields": ("tagline_en", "about_en")}),
        ("İletişim", {"fields": ("phone", "whatsapp", "email", "notify_email", "address",
                                 "instagram", "linkedin")}),
        ("Ana sayfa istatistikleri", {"fields": ("years_experience", "projects_done", "area_built")}),
    )

    def has_add_permission(self, request):
        # Singleton: only offer "add" until the one row exists.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "REN Yönetimi"
admin.site.site_title = "REN"
admin.site.index_title = "Yönetim paneli"
