from pathlib import Path
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from activities.models import Activity, ActivityImage
from hotels.models import Hotel, HotelImage, RoomImage, RoomType
from packages.models import PackageImage, TravelPackage


PALETTES = [
    ("#0f766e", "#f5b301", "#ffffff"),
    ("#1f7a8c", "#bfdbf7", "#ffffff"),
    ("#2f4858", "#f6ae2d", "#ffffff"),
    ("#3a7d44", "#d7f171", "#102a19"),
    ("#8d3b72", "#f7b2bd", "#ffffff"),
    ("#005f73", "#94d2bd", "#ffffff"),
]


class Command(BaseCommand):
    help = "Create local sample images for hotels, rooms, tours and activities."

    def handle(self, *args, **options):
        self.media_root = Path(settings.MEDIA_ROOT)
        self.font_large = self._font(36)
        self.font_medium = self._font(24)
        self.font_small = self._font(18)

        hotel_count = self.seed_hotels()
        room_count = self.seed_rooms()
        package_count = self.seed_packages()
        activity_count = self.seed_activities()

        self.stdout.write(self.style.SUCCESS(
            f"Created/verified images: hotels={hotel_count}, rooms={room_count}, "
            f"packages={package_count}, activities={activity_count}."
        ))

    def _font(self, size):
        for candidate in ("arial.ttf", "segoeui.ttf", "calibri.ttf"):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _safe_name(self, value):
        return slugify(value) or re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "image"

    def _relative_path(self, folder, title, index):
        return f"{folder}/{self._safe_name(title)}-{index}.png"

    def _create_image(self, relative_path, title, subtitle, palette_index):
        path = self.media_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return relative_path

        color_a, color_b, text_color = PALETTES[palette_index % len(PALETTES)]
        width, height = 1200, 780
        image = Image.new("RGB", (width, height), color_a)
        draw = ImageDraw.Draw(image)

        for y in range(height):
            ratio = y / max(height - 1, 1)
            r1, g1, b1 = tuple(int(color_a[i:i + 2], 16) for i in (1, 3, 5))
            r2, g2, b2 = tuple(int(color_b[i:i + 2], 16) for i in (1, 3, 5))
            color = (
                int(r1 + (r2 - r1) * ratio),
                int(g1 + (g2 - g1) * ratio),
                int(b1 + (b2 - b1) * ratio),
            )
            draw.line([(0, y), (width, y)], fill=color)

        draw.rectangle((70, 70, width - 70, height - 70), outline=text_color, width=4)
        draw.rectangle((100, height - 250, width - 100, height - 105), fill=(0, 0, 0, 96))

        self._multiline(draw, title, (125, height - 230), self.font_large, text_color, max_chars=30)
        self._multiline(draw, subtitle, (125, height - 145), self.font_medium, text_color, max_chars=48)
        draw.text((100, 100), "COTRIPVn", fill=text_color, font=self.font_small)

        image.save(path, quality=92)
        return relative_path

    def _multiline(self, draw, text, position, font, fill, max_chars):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            next_value = f"{current} {word}".strip()
            if len(next_value) > max_chars and current:
                lines.append(current)
                current = word
            else:
                current = next_value
        if current:
            lines.append(current)
        x, y = position
        for line in lines[:2]:
            draw.text((x, y), line, fill=fill, font=font)
            y += 42

    def seed_hotels(self):
        created = 0
        for hotel_index, hotel in enumerate(Hotel.objects.select_related("city").order_by("id")):
            for image_index, label in enumerate(("Exterior", "Lobby", "View"), start=1):
                relative_path = self._relative_path("hotels/generated", hotel.name, image_index)
                self._create_image(
                    relative_path,
                    hotel.name,
                    f"{label} - {hotel.city.name}",
                    hotel_index + image_index,
                )
                _, was_created = HotelImage.objects.get_or_create(
                    hotel=hotel,
                    image=relative_path,
                    defaults={
                        "caption": f"{label} {hotel.name}",
                        "alt_text": f"{hotel.name} {label}",
                        "category": "exterior" if image_index == 1 else "other",
                        "is_primary": image_index == 1 and not hotel.images.filter(is_primary=True).exists(),
                        "display_order": image_index,
                    },
                )
                created += int(was_created)
        return created

    def seed_rooms(self):
        created = 0
        for room_index, room in enumerate(RoomType.objects.select_related("hotel").order_by("id")):
            for image_index, label in enumerate(("Room", "Bathroom"), start=1):
                relative_path = self._relative_path("rooms/generated", f"{room.hotel.name}-{room.name}", image_index)
                self._create_image(
                    relative_path,
                    room.name,
                    f"{label} at {room.hotel.name}",
                    room_index + image_index,
                )
                _, was_created = RoomImage.objects.get_or_create(
                    room_type=room,
                    image=relative_path,
                    defaults={
                        "caption": f"{label} {room.name}",
                        "is_primary": image_index == 1 and not room.images.filter(is_primary=True).exists(),
                        "display_order": image_index,
                    },
                )
                created += int(was_created)
        return created

    def seed_packages(self):
        created = 0
        for package_index, package in enumerate(TravelPackage.objects.order_by("id")):
            for image_index, label in enumerate(("Overview", "Itinerary", "Experience"), start=1):
                relative_path = self._relative_path("packages/generated", package.title, image_index)
                self._create_image(
                    relative_path,
                    package.title,
                    f"{label} - {package.destination_city}",
                    package_index + image_index,
                )
                _, was_created = PackageImage.objects.get_or_create(
                    package=package,
                    image=relative_path,
                    defaults={
                        "caption": f"{label} {package.title}",
                        "alt_text": f"{package.title} {label}",
                        "is_primary": image_index == 1 and not package.images.filter(is_primary=True).exists(),
                        "display_order": image_index,
                    },
                )
                created += int(was_created)
        return created

    def seed_activities(self):
        created = 0
        for activity_index, activity in enumerate(Activity.objects.select_related("category").order_by("id")):
            for image_index, label in enumerate(("Main", "Guest moment", "Location"), start=1):
                relative_path = self._relative_path("activities/generated", activity.title, image_index)
                self._create_image(
                    relative_path,
                    activity.title,
                    f"{label} - {activity.city}",
                    activity_index + image_index,
                )
                _, was_created = ActivityImage.objects.get_or_create(
                    activity=activity,
                    image=relative_path,
                    defaults={
                        "caption": f"{label} {activity.title}",
                        "alt_text": f"{activity.title} {label}",
                        "is_primary": image_index == 1 and not activity.images.filter(is_primary=True).exists(),
                        "display_order": image_index,
                    },
                )
                created += int(was_created)
        return created
