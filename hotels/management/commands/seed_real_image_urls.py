import hashlib
from urllib.parse import quote

from django.core.management.base import BaseCommand

from activities.models import Activity, ActivityImage
from hotels.models import Hotel, HotelImage, RoomImage, RoomType
from packages.models import PackageImage, TravelPackage


def commons_file(filename):
    normalized = filename.replace(" ", "_")
    digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{quote(normalized)}"


CITY_IMAGES = {
    "Ha Noi": [
        commons_file("Ho Hoan Kiem.jpg"),
        commons_file("Hoan Kiem Lake.jpg"),
        commons_file("Hanoi Train Street 2020.jpg"),
    ],
    "Sa Pa": [
        commons_file("Terraced fields Sa Pa 6.jpg"),
        commons_file("Terraced fields Sa Pa 3.jpg"),
        commons_file("Sa Pa Vietnam.jpg"),
    ],
    "Ninh Binh": [
        commons_file("Vietnam, Ninh Binh, Trang An Limestone Peaks.jpg"),
        commons_file("Trang An Landscape Complex, Ninh Binh Province, Vietnam, 20240202 1524 5364.jpg"),
        commons_file("Trang An Landscape Complex, Ninh Binh Province, Vietnam, 20240202 1447 5310.jpg"),
    ],
    "Hoi An": [
        commons_file("Hoi An Ancient Town, Vietnam (7090653523).jpg"),
        commons_file("Hoi An Ancient Town, Vietnam (7090653523).jpg"),
        commons_file("Hoi An Ancient Town.jpg"),
    ],
    "Da Nang": [
        commons_file("Son Tra.jpg"),
        commons_file("My Khe Beach, Da Nang, Vietnam.jpg"),
        commons_file("My Khe Beach 14.jpg"),
    ],
    "Da Lat": [
        commons_file("Farm land in Da Lat, Vietnam.JPG"),
        commons_file("Xuan Huong Lake in Da Lat (28219543381).jpg"),
        commons_file("Da Lat, Vietnam - panoramio.jpg"),
    ],
    "Phu Quoc": [
        commons_file("Amazing beach on Phu Quoc island Vietnam (38647607275).jpg"),
        commons_file("Beach-3058750.jpg"),
        commons_file("Phu Quoc Beach.jpg"),
    ],
    "Ha Giang": [
        commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg"),
        commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg"),
        commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg"),
    ],
    "Hue": [
        commons_file("Imperial City, Hue, Vietnam (7073455889).jpg"),
        commons_file("Imperial City, Hue, Vietnam (49574906291).jpg"),
        commons_file("Perfume River Hue.jpg"),
    ],
    "Can Tho": [
        commons_file("Can Tho, Vietnam, Floating Market, Boats.jpg"),
        commons_file("Can tho floating market.jpg"),
        commons_file("Floating Market in Can Tho, Vietnam (5071426996).jpg"),
    ],
    "Ha Long": [
        commons_file("Ha Long bay, Vietnam.png"),
        commons_file("Ha Long Bay Vietnam.jpg"),
        commons_file("Halong Bay in Vietnam.jpg"),
    ],
    "Quy Nhon": [
        commons_file("View of Quy Nhon.jpg"),
        commons_file("Quy Nhon Beach Promenade.jpg"),
        commons_file("Ky Co beach, Quy Nhon city, Binh Dinh province, Vietnam.jpg"),
    ],
    "Con Dao": [
        commons_file("Con Dao sunset.jpg"),
        commons_file("Con dao 75 years.jpg"),
        commons_file("Con Dao.jpg"),
    ],
    "Mui Ne": [
        commons_file("Vietnam, Mui Ne sand dunes.jpg"),
        commons_file("Vietnam, Mui Ne sand dune.jpg"),
        commons_file("Vietnam, Mui Ne sand dunes, trees on the sand.jpg"),
    ],
    "Phong Nha": [
        commons_file("PhongNhaCave.jpg"),
        commons_file("PhongNhaCave2.jpg"),
        commons_file("Dong Hoi Phong Nha grotten.jpg"),
    ],
    "Nha Trang": [
        commons_file("Nha trang beach.jpg"),
        commons_file("Nha Trang beach.JPG"),
        commons_file("Hon Chong Nha Trang.jpg"),
    ],
    "TP. Ho Chi Minh": [
        commons_file("Ho Chi Minh City, Nguyen Hue Street, 2020-01 CN-03.jpg"),
        commons_file("Ho Chi Minh City skyline.jpg"),
        commons_file("Ben Thanh Market, Ho Chi Minh City.jpg"),
    ],
    "Moc Chau": [
        commons_file("Moc-chau-tea-doi-2094890 960 720.jpg"),
        commons_file("Moc Chau trong suong som (20880297811).jpg"),
        commons_file("Thacdaiyem.jpg"),
    ],
    "Dong Do": [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
    ],
    "Quan Lan": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1513415564515-763d91423bdd?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1513553404607-988bf2703777?auto=format&fit=crop&w=1200&q=80",
    ],
}

HOTEL_IMAGE_SETS = {
    "mountain": [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1510798831971-661eb04b3739?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1601919051950-bb9f3ffb3fee?auto=format&fit=crop&w=1200&q=80",
    ],
    "heritage": [
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1200&q=80",
    ],
    "beach": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    ],
    "city": [
        "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    ],
    "riverside": [
        "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1560448204-603b3fc33ddc?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1590490359683-658d3d23f972?auto=format&fit=crop&w=1200&q=80",
    ],
}

HOTEL_CITY_STYLE = {
    "Sa Pa": "mountain",
    "Ha Giang": "mountain",
    "Moc Chau": "mountain",
    "Da Lat": "mountain",
    "Ninh Binh": "heritage",
    "Hoi An": "heritage",
    "Hue": "heritage",
    "Phong Nha": "heritage",
    "Ha Noi": "city",
    "TP. Ho Chi Minh": "city",
    "Da Nang": "beach",
    "Nha Trang": "beach",
    "Phu Quoc": "beach",
    "Mui Ne": "beach",
    "Quy Nhon": "beach",
    "Con Dao": "beach",
    "Ha Long": "beach",
    "Can Tho": "riverside",
    "Dong Do": "mountain",
    "Quan Lan": "beach",
}

ACTIVITY_KEYWORD_IMAGES = {
    "dong do": [
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=1200&q=80",
    ],
    "quan lan": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1513415564515-763d91423bdd?auto=format&fit=crop&w=1200&q=80",
    ],
    "minh chau": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1513553404607-988bf2703777?auto=format&fit=crop&w=1200&q=80",
    ],
    "hoan kiem": [commons_file("Ho Hoan Kiem.jpg"), commons_file("Hoan Kiem Lake.jpg")],
    "old quarter": [commons_file("Ho Hoan Kiem.jpg"), commons_file("Hoan Kiem Lake.jpg")],
    "sapa": [commons_file("Terraced fields Sa Pa 6.jpg"), commons_file("Terraced fields Sa Pa 3.jpg")],
    "lao chai": [commons_file("Terraced fields Sa Pa 6.jpg"), commons_file("Terraced fields Sa Pa 3.jpg")],
    "ta van": [commons_file("Terraced fields Sa Pa 6.jpg"), commons_file("Terraced fields Sa Pa 3.jpg")],
    "fansipan": [commons_file("Terraced fields Sa Pa 6.jpg"), commons_file("Terraced fields Sa Pa 3.jpg")],
    "trang an": [commons_file("Vietnam, Ninh Binh, Trang An Limestone Peaks.jpg"), commons_file("Trang An Landscape Complex, Ninh Binh Province, Vietnam, 20240202 1524 5364.jpg")],
    "tam coc": [commons_file("Vietnam, Ninh Binh, Trang An Limestone Peaks.jpg"), commons_file("Trang An Landscape Complex, Ninh Binh Province, Vietnam, 20240202 1447 5310.jpg")],
    "hang mua": [commons_file("Vietnam, Ninh Binh, Trang An Limestone Peaks.jpg"), commons_file("Trang An Landscape Complex, Ninh Binh Province, Vietnam, 20240202 1524 5364.jpg")],
    "hoi an": [commons_file("Hoi An Ancient Town, Vietnam (7090653523).jpg"), commons_file("Hoi An Ancient Town.jpg")],
    "cam thanh": [commons_file("Hoi An Ancient Town, Vietnam (7090653523).jpg"), commons_file("Hoi An Ancient Town.jpg")],
    "an bang": [commons_file("Hoi An Ancient Town, Vietnam (7090653523).jpg"), commons_file("Hoi An Ancient Town.jpg")],
    "son tra": [commons_file("Son Tra.jpg"), commons_file("My Khe Beach, Da Nang.jpg")],
    "marble": [commons_file("Marble Mountains, Da Nang.jpg"), commons_file("Son Tra.jpg")],
    "da lat": [commons_file("Farm land in Da Lat, Vietnam.JPG"), commons_file("Xuan Huong Lake, Da Lat.jpg")],
    "tuyen lam": [commons_file("Farm land in Da Lat, Vietnam.JPG"), commons_file("Xuan Huong Lake, Da Lat.jpg")],
    "cau dat": [commons_file("Farm land in Da Lat, Vietnam.JPG"), commons_file("Dalat, Vietnam.jpg")],
    "phu quoc": [commons_file("Amazing beach on Phu Quoc island Vietnam (38647607275).jpg"), commons_file("Beach-3058750.jpg")],
    "starfish": [commons_file("Amazing beach on Phu Quoc island Vietnam (38647607275).jpg"), commons_file("Phu Quoc Beach.jpg")],
    "ha giang": [commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg"), commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg")],
    "quan ba": [commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg"), commons_file("Ma Pi Leng Pass winding road Ha Giang Vietnam.jpg")],
    "mui ne": [commons_file("Vietnam, Mui Ne sand dunes.jpg"), commons_file("Vietnam, Mui Ne sand dune.jpg")],
    "sand dunes": [commons_file("Vietnam, Mui Ne sand dunes.jpg"), commons_file("Vietnam, Mui Ne sand dune.jpg")],
    "can tho": [commons_file("Can Tho, Vietnam, Floating Market, Boats.jpg"), commons_file("Can tho floating market.jpg")],
    "floating market": [commons_file("Can Tho, Vietnam, Floating Market, Boats.jpg"), commons_file("Floating Market in Can Tho, Vietnam (5071426996).jpg")],
    "hue": [commons_file("Imperial City, Hue, Vietnam (7073455889).jpg"), commons_file("Imperial City, Hue, Vietnam (49574906291).jpg")],
    "imperial": [commons_file("Imperial City, Hue, Vietnam (7073455889).jpg"), commons_file("Imperial City, Hue, Vietnam (49574906291).jpg")],
    "ha long": [commons_file("Ha Long bay, Vietnam.png"), commons_file("Ha Long Bay Vietnam.jpg")],
    "phong nha": [commons_file("PhongNhaCave.jpg"), commons_file("PhongNhaCave2.jpg")],
    "nha trang": [commons_file("Nha trang beach.jpg"), commons_file("Nha Trang beach.JPG")],
    "cu chi": [commons_file("Cu Chi Tunnels.jpg"), commons_file("Cu Chi tunnel entrance.jpg")],
    "ho thi ky": [commons_file("Ben Thanh Market, Ho Chi Minh City.jpg"), commons_file("Ho Chi Minh City skyline.jpg")],
    "saigon": [commons_file("Ho Chi Minh City, Nguyen Hue Street, 2020-01 CN-03.jpg"), commons_file("Ho Chi Minh City skyline.jpg")],
    "moc chau": [commons_file("Moc-chau-tea-doi-2094890 960 720.jpg"), commons_file("Moc Chau trong suong som (20880297811).jpg")],
    "quy nhon": [commons_file("View of Quy Nhon.jpg"), commons_file("Quy Nhon Beach Promenade.jpg")],
    "con dao": [commons_file("Con Dao sunset.jpg"), commons_file("Con dao 75 years.jpg")],
}

ROOM_IMAGES = [
    "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1200&q=80",
]


class Command(BaseCommand):
    help = "Attach destination-accurate external image URLs for hotels, rooms, packages and activities."

    def handle(self, *args, **options):
        hotel_updates = self.seed_hotels()
        room_updates = self.seed_rooms()
        package_updates = self.seed_packages()
        activity_updates = self.seed_activities()
        self.stdout.write(self.style.SUCCESS(
            f"External image URLs attached: hotels={hotel_updates}, rooms={room_updates}, "
            f"packages={package_updates}, activities={activity_updates}."
        ))

    def image_set_for_city(self, city_name):
        return CITY_IMAGES.get(city_name) or CITY_IMAGES["Ha Noi"]

    def image_set_for_hotel(self, hotel):
        style = HOTEL_CITY_STYLE.get(hotel.city.name, "city")
        images = HOTEL_IMAGE_SETS[style]
        offset = hotel.id % len(images)
        return images[offset:] + images[:offset]

    def image_set_for_text(self, text, city_name=""):
        text_key = text.lower()
        for keyword, images in ACTIVITY_KEYWORD_IMAGES.items():
            if keyword in text_key:
                return images
        return self.image_set_for_city(city_name)

    def seed_hotels(self):
        updates = 0
        for hotel in Hotel.objects.select_related("city").order_by("id"):
            images = self.image_set_for_hotel(hotel)
            hotel.image_url = images[0]
            hotel.save(update_fields=["image_url", "updated_at"])
            for image_index, external_url in enumerate(images[:3]):
                image, _ = HotelImage.objects.update_or_create(
                    hotel=hotel,
                    display_order=image_index + 1,
                    defaults={
                        "external_url": external_url,
                        "caption": f"{hotel.name} accommodation reference image",
                        "alt_text": f"{hotel.name} accommodation image",
                        "category": "exterior" if image_index == 0 else "room",
                        "is_primary": image_index == 0,
                    },
                )
                if image_index == 0:
                    HotelImage.objects.filter(hotel=hotel).exclude(id=image.id).update(is_primary=False)
                updates += 1
        return updates

    def seed_rooms(self):
        updates = 0
        for room_index, room in enumerate(RoomType.objects.select_related("hotel").order_by("id")):
            for image_index in range(2):
                external_url = ROOM_IMAGES[(room_index + image_index) % len(ROOM_IMAGES)]
                image, _ = RoomImage.objects.update_or_create(
                    room_type=room,
                    display_order=image_index + 1,
                    defaults={
                        "external_url": external_url,
                        "caption": f"{room.name} room reference image",
                        "is_primary": image_index == 0,
                    },
                )
                if image_index == 0:
                    RoomImage.objects.filter(room_type=room).exclude(id=image.id).update(is_primary=False)
                updates += 1
        return updates

    def seed_packages(self):
        updates = 0
        for package in TravelPackage.objects.order_by("id"):
            images = self.image_set_for_text(package.title, package.destination_city)
            package.image_url = images[0]
            package.save(update_fields=["image_url", "updated_at"])
            for image_index, external_url in enumerate(images[:3]):
                image, _ = PackageImage.objects.update_or_create(
                    package=package,
                    display_order=image_index + 1,
                    defaults={
                        "external_url": external_url,
                        "caption": f"{package.title} destination image",
                        "alt_text": f"{package.title} tour image",
                        "is_primary": image_index == 0,
                    },
                )
                if image_index == 0:
                    PackageImage.objects.filter(package=package).exclude(id=image.id).update(is_primary=False)
                updates += 1
        return updates

    def seed_activities(self):
        updates = 0
        for activity in Activity.objects.order_by("id"):
            images = self.image_set_for_text(activity.title, activity.city)
            activity.image_url = images[0]
            activity.save(update_fields=["image_url", "updated_at"])
            for image_index, external_url in enumerate(images[:3]):
                image, _ = ActivityImage.objects.update_or_create(
                    activity=activity,
                    display_order=image_index + 1,
                    defaults={
                        "external_url": external_url,
                        "caption": f"{activity.title} destination image",
                        "alt_text": f"{activity.title} in {activity.city}",
                        "is_primary": image_index == 0,
                    },
                )
                if image_index == 0:
                    ActivityImage.objects.filter(activity=activity).exclude(id=image.id).update(is_primary=False)
                updates += 1
        return updates
