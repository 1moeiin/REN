"""Fills the site with realistic starter content: `manage.py seed_demo`.

Idempotent — re-running updates the same rows instead of duplicating them.
"""

from django.core.management.base import BaseCommand

from main.models import ProcessStep, Project, Reference, Service, SiteSettings

SERVICES = [
    ("Konut İnşaatı", "konut-insaati", "building",
     "Hafriyattan anahtar teslimine kadar konut projelerinin eksiksiz uygulaması, "
     "kesintisiz mühendislik denetimiyle."),
    ("Ticari ve Ofis Projeleri", "ticari-ofis", "crane",
     "Alışveriş merkezleri, ofis blokları ve perakende alanlarının güncel "
     "standartlara uygun tasarımı ve inşası."),
    ("Mimari Tasarım", "mimari-tasarim", "ruler",
     "Uygulama başlamadan önce mimari tasarım, uygulama projeleri ve üç boyutlu "
     "modelleme."),
    ("Renovasyon ve Güçlendirme", "renovasyon", "wrench",
     "Eski yapıların komple yenilenmesi ve taşıyıcı sistemin depreme karşı "
     "güçlendirilmesi."),
    ("Proje Yönetimi", "proje-yonetimi", "hardhat",
     "Yapım yönetimi, maliyet ve zaman kontrolü, malzeme tedariği."),
    ("Yeşil Bina", "yesil-bina", "leaf",
     "Doğru yalıtım ve enerji geri kazanım sistemleriyle düşük tüketimli binalar."),
]

PROJECTS = [
    ("Arman Rezidans", "arman-rezidans", "residential", "completed",
     "60 daireli, dubleks lobili ve katlı otoparklı 15 katlı konut kulesi.",
     "İstanbul, Ataşehir", "Arman Yatırım Grubu", 12400, 2023, True),
    ("Negin Ticaret Merkezi", "negin-ticaret-merkezi", "commercial", "completed",
     "45 ticari üniteli ve merkezi yemek katlı üç katlı alışveriş merkezi.",
     "İzmir, Bornova", "Negin Geliştirme A.Ş.", 8600, 2022, True),
    ("Pars Endüstri Fabrikası", "pars-endustri", "industrial", "completed",
     "Çelik konstrüksiyonlu endüstriyel tesis, idari ofis ve kapalı depo.",
     "Kocaeli, Gebze OSB", "Pars Endüstri", 15000, 2021, True),
    ("Beşiktaş Ofis Yenileme", "besiktas-ofis-yenileme", "renovation", "ongoing",
     "Eski bir ofis binasının cephe, tesisat ve taşıyıcı sistem güçlendirmesiyle "
     "komple yenilenmesi.",
     "İstanbul, Beşiktaş", "Özel sektör", 3200, 2024, True),
    ("Sahil Villaları", "sahil-villalari", "residential", "ongoing",
     "Peyzaj düzenlemesi ve ortak havuzlu 18 adet dubleks villa.",
     "Muğla, Bodrum", "Deniz Konut Kooperatifi", 6800, 2024, True),
    ("Doğu Lojistik Merkezi", "dogu-lojistik-merkezi", "industrial", "planned",
     "Yükleme rampalı mekanize depo ve iki katlı idari bina.",
     "Ankara, Kazan", "Doğu Holding", 22000, 2025, False),
]


STEPS = [
    ("Keşif ve analiz", "Survey & analysis",
     "Arsa incelemesi, imar durumu ve ihtiyaç programının çıkarılması.",
     "Site inspection, zoning status and drawing up the requirements brief.",
     "1-2 hafta"),
    ("Tasarım ve projelendirme", "Design & documentation",
     "Mimari tasarım, statik ve tesisat projeleri, ruhsat dosyası.",
     "Architectural design, structural and MEP drawings, permit file.",
     "4-8 hafta"),
    ("Uygulama", "Construction",
     "Şantiye kurulumu, imalat ve haftalık ilerleme raporlaması.",
     "Site setup, construction and weekly progress reporting.",
     "Projeye göre"),
    ("Teslim ve garanti", "Handover & warranty",
     "Kabul testleri, anahtar teslimi ve garanti dönemi takibi.",
     "Acceptance testing, key handover and warranty period follow-up.",
     "2 yıl garanti"),
]

REFERENCES = [
    ("Arman Yatırım Grubu", "client"),
    ("Negin Geliştirme A.Ş.", "client"),
    ("Pars Endüstri", "client"),
    ("Doğu Holding", "client"),
    ("Deniz Konut Kooperatifi", "client"),
    ("ISO 9001 Kalite Yönetimi", "certificate"),
    ("ISO 45001 İş Sağlığı ve Güvenliği", "certificate"),
    ("İstanbul Ticaret Odası Üyesi", "certificate"),
    ("Yapı Müteahhitliği Yetki Belgesi", "certificate"),
]


class Command(BaseCommand):
    help = "Örnek site içeriği oluşturur"

    def handle(self, *args, **options):
        site = SiteSettings.load()
        site.company_name = "REN Yapı"
        site.tagline = "Kaliteye ve takvime bağlı kalarak inşaat projeleri tasarlıyor ve uyguluyoruz"
        site.about = (
            "REN Yapı, 2004 yılından bu yana inşaat projelerinin tasarımı ve uygulaması "
            "alanında faaliyet göstermektedir. Odağımız uygulama kalitesi, takvime "
            "bağlılık ve maliyetlerde şeffaflıktır.\n\n"
            "Ekibimiz, 120'den fazla konut, ticari ve endüstriyel projede birlikte "
            "çalışmış inşaat mühendisleri, mimarlar ve proje yöneticilerinden oluşur."
        )
        site.tagline_en = "We design and build construction projects, committed to quality and schedule"
        site.about_en = (
            "REN Yapı has been designing and delivering construction projects since 2004. "
            "Our focus is execution quality, keeping to schedule and transparency on cost.\n\n"
            "Our team is made up of civil engineers, architects and project managers who have "
            "worked together on more than 120 residential, commercial and industrial projects."
        )
        site.phone = "+90 212 555 66 77"
        site.whatsapp = "905321234567"
        site.notify_email = "info@renyapi.com.tr"
        site.email = "info@renyapi.com.tr"
        site.address = "Büyükdere Caddesi No: 120, Şişli, İstanbul"
        site.years_experience = 20
        site.projects_done = 124
        site.area_built = 480000
        site.save()
        self.stdout.write("✓ Site ayarları")

        for order, (title, slug, icon, summary) in enumerate(SERVICES):
            Service.objects.update_or_create(
                slug=slug,
                defaults={"title": title, "icon": icon, "summary": summary, "order": order},
            )
        self.stdout.write(f"✓ {len(SERVICES)} hizmet")

        for order, (title, slug, cat, status, summary, loc, client, area, year, feat) in enumerate(PROJECTS):
            Project.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title, "category": cat, "status": status, "summary": summary,
                    "location": loc, "client": client, "area_m2": area, "year": year,
                    "is_featured": feat, "order": order,
                    "description": f"{summary}\n\nBu proje {loc} konumunda, {client} için gerçekleştirilmiştir.",
                },
            )
        self.stdout.write(f"✓ {len(PROJECTS)} proje")
        for order, (title, t_en, desc, d_en, dur) in enumerate(STEPS):
            ProcessStep.objects.update_or_create(
                order=order,
                defaults={"title": title, "title_en": t_en, "description": desc,
                          "description_en": d_en, "duration": dur},
            )
        self.stdout.write(f"✓ {len(STEPS)} süreç adımı")

        for order, (name, kind) in enumerate(REFERENCES):
            Reference.objects.update_or_create(
                name=name, defaults={"kind": kind, "order": order}
            )
        self.stdout.write(f"✓ {len(REFERENCES)} referans")

        self.stdout.write(self.style.SUCCESS("Örnek içerik oluşturuldu."))
