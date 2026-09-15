"""Generate WebP siblings for uploaded images: `manage.py optimize_images`.

Uploads come straight from a phone or a render, often several MB. This writes a
`<name>.webp` next to each one and the template's <picture> prefers it, so
browsers that support WebP fetch far less. The original is never touched, so
the command is safe to re-run and safe to skip.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image

SOURCE_SUFFIXES = {".jpg", ".jpeg", ".png"}
MAX_WIDTH = 2000


class Command(BaseCommand):
    help = "Uploaded görselleri WebP'e dönüştürür"

    def add_arguments(self, parser):
        parser.add_argument("--quality", type=int, default=82)
        parser.add_argument("--force", action="store_true", help="Var olan .webp dosyalarını yeniden üret")

    def handle(self, *args, **options):
        root = Path(settings.MEDIA_ROOT)
        if not root.exists():
            self.stdout.write("media/ yok — atlanıyor.")
            return

        made = skipped = 0
        saved_bytes = 0

        for src in sorted(root.rglob("*")):
            if src.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            dest = src.with_suffix(".webp")
            if dest.exists() and not options["force"]:
                skipped += 1
                continue

            with Image.open(src) as im:
                im = im.convert("RGB")
                if im.width > MAX_WIDTH:
                    im = im.resize(
                        (MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS
                    )
                im.save(dest, "WEBP", quality=options["quality"], method=6)

            delta = src.stat().st_size - dest.stat().st_size
            if delta <= 0:
                # An already-small, heavily-compressed JPEG can come out LARGER
                # as WebP. Keeping it would make the page slower, so drop it and
                # let the template fall back to the original.
                dest.unlink()
                skipped += 1
                self.stdout.write(f"  {src.relative_to(root)} — WebP daha büyük, atlandı")
                continue

            saved_bytes += delta
            made += 1
            self.stdout.write(
                f"  {src.relative_to(root)} → .webp "
                f"({src.stat().st_size // 1024}K → {dest.stat().st_size // 1024}K)"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{made} dosya dönüştürüldü, {skipped} atlandı, "
                f"~{saved_bytes // 1024}K kazanıldı."
            )
        )
