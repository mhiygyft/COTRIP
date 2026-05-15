from django.core.management.base import BaseCommand

from activities.models import Activity, ActivityImage
from hotels.models import Hotel, HotelImage, RoomImage, RoomType
from packages.models import PackageImage, TravelPackage


HOTEL_IMAGES = [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
]

ROOM_IMAGES = [
    "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1200&q=80",
]

TOUR_IMAGES = [
    "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1513415564515-763d91423bdd?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?auto=format&fit=crop&w=1200&q=80",
]

ACTIVITY_IMAGES = [
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1513553404607-988bf2703777?auto=format&fit=crop&w=1200&q=80",
]


class Command(BaseCommand):
    help = "Attach real external image URLs for customer-facing hotel, room, package and activity galleries."

    def handle(self, *args, **options):
        hotel_updates = self.seed_hotels()
        room_updates = self.seed_rooms()
        package_updates = self.seed_packages()
        activity_updates = self.seed_activities()
        self.stdout.write(self.style.SUCCESS(
            f"Real image URLs attached: hotels={hotel_updates}, rooms={room_updates}, "
            f"packages={package_updates}, activities={activity_updates}."
        ))

    def seed_hotels(self):
        updates = 0
        for hotel_index, hotel in enumerate(Hotel.objects.order_by("id")):
            hotel.image_url = ""
            hotel.save(update_fields=["image_url", "updated_at"])
            for image_index in range(3):
                image, _ = HotelImage.objects.get_or_create(
                    hotel=hotel,
                    display_order=image_index + 1,
                    defaults={
                        "caption": f"{hotel.name} real photo {image_index + 1}",
                        "alt_text": f"{hotel.name} real photo",
                        "category": "exterior" if image_index == 0 else "other",
                        "is_primary": image_index == 0,
                    },
                )
                image.external_url = HOTEL_IMAGES[(hotel_index + image_index) % len(HOTEL_IMAGES)]
                image.is_primary = image_index == 0
                image.save(update_fields=["external_url", "is_primary"])
                updates += 1
        return updates

    def seed_rooms(self):
        updates = 0
        for room_index, room in enumerate(RoomType.objects.select_related("hotel").order_by("id")):
            for image_index in range(2):
                image, _ = RoomImage.objects.get_or_create(
                    room_type=room,
                    display_order=image_index + 1,
                    defaults={
                        "caption": f"{room.name} real room photo {image_index + 1}",
                        "is_primary": image_index == 0,
                    },
                )
                image.external_url = ROOM_IMAGES[(room_index + image_index) % len(ROOM_IMAGES)]
                image.is_primary = image_index == 0
                image.save(update_fields=["external_url", "is_primary"])
                updates += 1
        return updates

    def seed_packages(self):
        updates = 0
        for package_index, package in enumerate(TravelPackage.objects.order_by("id")):
            package.image_url = ""
            package.save(update_fields=["image_url", "updated_at"])
            for image_index in range(3):
                image, _ = PackageImage.objects.get_or_create(
                    package=package,
                    display_order=image_index + 1,
                    defaults={
                        "caption": f"{package.title} real tour photo {image_index + 1}",
                        "alt_text": f"{package.title} real tour photo",
                        "is_primary": image_index == 0,
                    },
                )
                image.external_url = TOUR_IMAGES[(package_index + image_index) % len(TOUR_IMAGES)]
                image.is_primary = image_index == 0
                image.save(update_fields=["external_url", "is_primary"])
                updates += 1
        return updates

    def seed_activities(self):
        updates = 0
        for activity_index, activity in enumerate(Activity.objects.order_by("id")):
            activity.image_url = ""
            activity.save(update_fields=["image_url", "updated_at"])
            for image_index in range(3):
                image, _ = ActivityImage.objects.get_or_create(
                    activity=activity,
                    display_order=image_index + 1,
                    defaults={
                        "caption": f"{activity.title} real activity photo {image_index + 1}",
                        "alt_text": f"{activity.title} real activity photo",
                        "is_primary": image_index == 0,
                    },
                )
                image.external_url = ACTIVITY_IMAGES[(activity_index + image_index) % len(ACTIVITY_IMAGES)]
                image.is_primary = image_index == 0
                image.save(update_fields=["external_url", "is_primary"])
                updates += 1
        return updates
