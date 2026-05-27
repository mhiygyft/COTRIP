from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from activities.models import Activity, ActivityCategory, ActivityImage
from hotels.models import Amenity, City, Country, Hotel, HotelImage, RoomAvailability, RoomType


SOURCE_NOTE = "Du lieu tham khao tu nguon cong khai: {source}"


class Command(BaseCommand):
    help = "Seed youth-oriented homestays, cafes, small viewpoints and trendy local attractions."

    def handle(self, *args, **options):
        with transaction.atomic():
            country = self.ensure_country()
            cities = self.ensure_cities(country)
            amenities = self.ensure_amenities()
            homestays = self.seed_homestays(cities, amenities)
            hotspots = self.seed_hotspots()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded/updated {len(homestays)} homestays and {len(hotspots)} youth hotspots."
        ))

    def ensure_country(self):
        country, _ = Country.objects.get_or_create(
            name="Viet Nam",
            defaults={"code": "VNM", "is_popular": True},
        )
        return country

    def ensure_cities(self, country):
        city_names = [
            "Ha Noi", "Sa Pa", "Ninh Binh", "Ha Long", "Hue", "Da Nang",
            "Hoi An", "Nha Trang", "Da Lat", "TP. Ho Chi Minh", "Can Tho",
            "Phu Quoc", "Phong Nha", "Ha Giang", "Mui Ne", "Quy Nhon",
            "Con Dao", "Moc Chau",
        ]
        cities = {}
        for name in city_names:
            city, _ = City.objects.get_or_create(
                name=name,
                country=country,
                defaults={"is_popular": True, "description": f"Diem den du lich {name}."},
            )
            cities[name] = city
        return cities

    def ensure_amenities(self):
        rows = [
            ("Wi-Fi mien phi", "internet", "bi bi-wifi"),
            ("Goc check-in", "entertainment", "bi bi-camera"),
            ("Cafe / rooftop", "food_drink", "bi bi-cup-hot"),
            ("Thue xe may", "transportation", "bi bi-scooter"),
            ("Bep chung", "general", "bi bi-egg-fried"),
            ("View nui/ruong", "recreation", "bi bi-mountain"),
            ("Gan pho di bo/cho dem", "general", "bi bi-signpost"),
        ]
        amenities = []
        for name, category, icon in rows:
            amenity, _ = Amenity.objects.get_or_create(
                name=name,
                defaults={"category": category, "icon": icon, "is_popular": True},
            )
            amenities.append(amenity)
        return amenities

    def seed_homestays(self, cities, amenities):
        rows = [
            ("Ta Van Cloud View Homestay", "Sa Pa", "Homestay trong thung lung Ta Van, view ruong bac thang va nui Hoang Lien Son.", 650000, "https://www.vietnam.travel/places-to-go/northern-vietnam/sapa", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Cat Cat Art House", "Sa Pa", "Nha go phong cach ban lang, phu hop nhom ban thich trekking va chup anh.", 520000, "https://vietnamtourism.gov.vn/en/printer/15363?type=1", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Gem Valley Inspired Stay", "Sa Pa", "Luu tru gan Cat Cat, ket hop cafe, tranh va view thung lung.", 720000, "https://en.wikivoyage.org/wiki/Sa_Pa", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Tam Coc Rice Field Bungalow", "Ninh Binh", "Bungalow giua dong lua Tam Coc, tien dap xe, thuyen Trang An va Hang Mua.", 780000, "https://en.wikivoyage.org/wiki/Ninh_Binh", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
            ("Trang An Garden Homestay", "Ninh Binh", "Homestay vuon yen tinh gan Trang An, hop cap doi va nhom nho.", 690000, "https://en.wikipedia.org/wiki/Tr%C3%A0ng_An_Scenic_Landscape_Complex", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
            ("Hoi An Rice Field Home", "Hoi An", "Nha nho gan dong lua, dap xe vao pho co va cafe san vuon.", 620000, "https://www.vietnam.travel/things-to-do/the-best-ways-to-explore-the-ancient-town-of-hoi-an", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Cam Thanh Coconut Stay", "Hoi An", "Homestay gan rung dua Bay Mau, tien di thuyen thung va lop nau an.", 580000, "https://vietnamtourism.gov.vn/en/post/19129", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Da Nang Beach Studio", "Da Nang", "Studio toi gian gan My Khe, phu hop khach tre thich bien va cafe.", 850000, "https://en.wikivoyage.org/wiki/Da_Nang", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("An Thuong Social Homestay", "Da Nang", "Luu tru khu An Thuong nhieu quan an, bar nho va cafe quoc te.", 760000, "https://en.wikivoyage.org/wiki/Da_Nang", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Da Lat Pine Hill Homestay", "Da Lat", "Nha go giua doi thong, phu hop san may, picnic va nhom ban.", 720000, "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Da Lat Vintage Attic", "Da Lat", "Homestay vintage gan trung tam, thich hop check-in, cho dem va cafe.", 590000, "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Phu Quoc Sunset Local Stay", "Phu Quoc", "Local stay gan bien, hop di tour nam dao va ngam hoang hon.", 880000, "https://en.wikivoyage.org/wiki/Phu_Quoc", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Ha Giang Loop Hostel", "Ha Giang", "Hostel cho nhom di Ha Giang Loop, co san xe may va lich trinh goi y.", 420000, "https://en.wikivoyage.org/wiki/Ha_Giang", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Phong Nha Farmstay Corner", "Phong Nha", "Nha nghi nho gan dong Phong Nha, hop khach thich hang dong va thien nhien.", 640000, "https://en.wikipedia.org/wiki/Phong_Nha%E2%80%93K%E1%BA%BB_B%C3%A0ng_National_Park", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
            ("Mui Ne Sand Dune Chill House", "Mui Ne", "Homestay gan doi cat, phu hop ngam binh minh, jeep tour va bien.", 690000, "https://en.wikivoyage.org/wiki/Mui_Ne", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Truc Bach Local Loft", "Ha Noi", "Can ho local gan ho Truc Bach, tien di bo cafe, pho co va cac quan an nho.", 780000, "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80"),
            ("Thao Dien Social Stay", "TP. Ho Chi Minh", "Local stay khu Thao Dien, hop khach tre thich cafe, brunch va song Sai Gon.", 920000, "https://en.wikivoyage.org/wiki/Ho_Chi_Minh_City", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Hue Garden Local House", "Hue", "Nha vuon nho gan khu trung tam Hue, phu hop lich trinh lang tam, song Huong va cafe.", 610000, "https://www.vietnam.travel/places-to-go/central-vietnam/hue", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("Can Tho Riverside Homestay", "Can Tho", "Homestay ven song cho nhom muon di cho noi Cai Rang, vuon trai cay va food tour dem.", 540000, "https://en.wikivoyage.org/wiki/Can_Tho", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Ha Long Fisherman Stay", "Ha Long", "Local stay gan Bai Chay, tien di vinh, cho dem va cac quan hai san nho.", 760000, "https://vietnamtourism.gov.vn/en/post/16441", "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80"),
            ("Quy Nhon Surf House", "Quy Nhon", "Nha nghi nho gan bien, phu hop nhom ban thich Ky Co, Eo Gio va cafe bien.", 680000, "https://en.wikivoyage.org/wiki/Quy_Nhon", "https://images.unsplash.com/photo-1513553404607-988bf2703777?auto=format&fit=crop&w=1200&q=80"),
            ("Con Dao Slow Stay", "Con Dao", "Local stay yen tinh cho lich trinh bien, hon nho va cac diem lich su Con Dao.", 980000, "https://en.wikivoyage.org/wiki/Con_Dao", "https://images.unsplash.com/photo-1513415564515-763d91423bdd?auto=format&fit=crop&w=1200&q=80"),
            ("Moc Chau Valley Cabin", "Moc Chau", "Cabin nho gan doi che, thung lung va cac diem chup anh theo mua hoa.", 650000, "https://en.wikivoyage.org/wiki/Moc_Chau", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
        ]

        homestays = []
        for name, city_name, text, price, source, image in rows:
            hotel, _ = Hotel.objects.update_or_create(
                slug=slugify(f"{name}-{city_name}"),
                defaults={
                    "name": name,
                    "city": cities[city_name],
                    "address": city_name,
                    "description": f"{text}\n\n{SOURCE_NOTE.format(source=source)}",
                    "star_rating": 3,
                    "image_url": image,
                    "price_from": Decimal(price),
                    "currency": "VND",
                    "is_active": True,
                    "is_featured": city_name in {"Sa Pa", "Ninh Binh", "Da Lat", "Hoi An", "Ha Noi"},
                    "is_verified": True,
                    "total_rooms": 8,
                    "average_rating": Decimal("8.8"),
                    "total_reviews": 120,
                    "meta_title": name,
                    "meta_description": text[:300],
                },
            )
            hotel.amenities.set(amenities)
            HotelImage.objects.update_or_create(
                hotel=hotel,
                is_primary=True,
                defaults={
                    "external_url": image,
                    "caption": name,
                    "alt_text": name,
                    "category": "exterior",
                    "display_order": 0,
                },
            )
            room, _ = RoomType.objects.update_or_create(
                hotel=hotel,
                slug="cozy-homestay-room",
                defaults={
                    "name": "Cozy Homestay Room",
                    "description": "Phong rieng day du tien nghi co goc check-in va khong gian sinh hoat chung.",
                    "size_sqm": 24,
                    "max_occupancy": 2,
                    "max_adults": 2,
                    "max_children": 1,
                    "bed_type": "queen",
                    "number_of_beds": 1,
                    "base_price": Decimal(price),
                    "is_refundable": True,
                    "free_cancellation_hours": 24,
                    "is_active": True,
                    "total_rooms": 8,
                },
            )
            room.amenities.set(amenities[:4])
            self.seed_availability(room, Decimal(price))
            homestays.append(hotel)
        return homestays

    def seed_availability(self, room, price):
        today = timezone.localdate()
        for offset in range(90):
            stay_date = today + timedelta(days=offset)
            weekend_multiplier = Decimal("1.15") if stay_date.weekday() >= 5 else Decimal("1.00")
            RoomAvailability.objects.update_or_create(
                room_type=room,
                date=stay_date,
                defaults={
                    "available_rooms": 5,
                    "price": (price * weekend_multiplier).quantize(Decimal("1")),
                    "is_weekend": stay_date.weekday() >= 5,
                    "is_holiday": False,
                    "demand_multiplier": weekend_multiplier,
                },
            )

    def seed_hotspots(self):
        categories = self.ensure_activity_categories()
        rows = [
            ("The Haven Sapa Campsite View Cafe", "Sa Pa", "Cafe san may va view Cat Cat, hop check-in nhom ban.", 120000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Sa_Pa", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Gem Valley Cat Cat Art Cafe", "Sa Pa", "Quan cafe ket hop khong gian nghe thuat va homestay gan Cat Cat.", 90000, "Cafe/check-in", "https://vietnamtourism.gov.vn/en/printer/15363?type=1", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Hang Mua Sunset Viewpoint", "Ninh Binh", "Leo nui ngam Tam Coc, song nui va hoang hon.", 180000, "Viewpoint", "https://en.wikivoyage.org/wiki/Ninh_Binh", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
            ("Sister Fields Ninh Binh Cafe", "Ninh Binh", "Cafe yen tinh trong hem nho, phu hop nghi giua lich trinh Trang An/Tam Coc.", 110000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Ninh_Binh", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Hoi An Rooftop Cafe Trail", "Hoi An", "Cung duong cafe rooftop va hem nho trong pho co Hoi An.", 150000, "Cafe/check-in", "https://www.vietnam.travel/things-to-do/the-best-ways-to-explore-the-ancient-town-of-hoi-an", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Cam Thanh Basket Boat Mini Tour", "Hoi An", "Tour thuyen thung ngan, chup anh rung dua va thu do an dia phuong.", 320000, "Local experience", "https://vietnamtourism.gov.vn/en/post/19129", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("An Bang Beach Chill Afternoon", "Hoi An", "Buoi chieu bien An Bang, beach bar nho va hoang hon.", 160000, "Local experience", "https://en.wikivoyage.org/wiki/Hoi_An", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Son Tra Peninsula Photo Stop", "Da Nang", "Cung duong Son Tra, bien, rung va cac diem dung chup anh.", 280000, "Viewpoint", "https://en.wikivoyage.org/wiki/Da_Nang", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Nam O Reef Morning Check-in", "Da Nang", "Bai da reu va bien sang som, hop chup anh nhe nhang.", 120000, "Viewpoint", "https://en.wikivoyage.org/wiki/Da_Nang", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Binh Minh Oi Coffee Dalat", "Da Lat", "Cafe view doi va khong gian go vintage duoc gioi tre yeu thich.", 130000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Cau Dat Cloud Hunting", "Da Lat", "San may, doi che va cung duong chup anh ngoai o Da Lat.", 260000, "Viewpoint", "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Tuyen Lam Picnic Corner", "Da Lat", "Picnic ho Tuyen Lam, rung thong va SUP/chill nhe.", 350000, "Local experience", "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Grand World Phu Quoc Evening Walk", "Phu Quoc", "Check-in thanh pho khong ngu, kenh dao va show dem.", 200000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Phu_Quoc", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Phu Quoc Starfish Beach Mini Trip", "Phu Quoc", "Chuyen di nua ngay den bai bien phia Bac, chup anh va hai san.", 450000, "Local experience", "https://en.wikivoyage.org/wiki/Phu_Quoc", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Truc Bach Hidden Cafe Walk", "Ha Noi", "Di bo quanh Truc Bach, cafe nho, ho va cac goc pho it on ao.", 180000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80"),
            ("Tay Ho Sunset Coffee Route", "Ha Noi", "Cung ho Tay, cafe ngam hoang hon va diem chup anh ven ho.", 160000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80"),
            ("Ha Giang Quan Ba Photo Stop", "Ha Giang", "Diem dung check-in cong troi Quan Ba tren cung Ha Giang Loop.", 250000, "Viewpoint", "https://en.wikivoyage.org/wiki/Ha_Giang", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Mui Ne White Sand Dunes Sunrise", "Mui Ne", "Jeep tour binh minh tai doi cat trang, ho sen va bien Mui Ne.", 420000, "Viewpoint", "https://en.wikivoyage.org/wiki/Mui_Ne", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Quang Phu Cau Incense Village", "Ha Noi", "Lang nghe huong ngoai thanh Ha Noi, hop chup anh mau sac va tim hieu san xuat thu cong.", 260000, "Local experience", "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80"),
            ("Train Street Coffee Window", "Ha Noi", "Trai nghiem cafe pho duong tau theo khung gio an toan va huong dan dia phuong.", 180000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80"),
            ("Tra Que Vegetable Village Bike Stop", "Hoi An", "Dap xe den lang rau Tra Que, chup anh dong rau va thu mot bua nhe dia phuong.", 280000, "Local experience", "https://en.wikipedia.org/wiki/Tr%C3%A0_Qu%E1%BA%BF_Vegetable_Village", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Ho Thi Ky Flower Market Food Walk", "TP. Ho Chi Minh", "Di cho hoa va an vat khu Ho Thi Ky ve toi, hop nhom ban thich am thuc duong pho.", 320000, "Local experience", "https://en.wikivoyage.org/wiki/Ho_Chi_Minh_City", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Saigon River Sunset Waterbus", "TP. Ho Chi Minh", "Di waterbus/ngam song Sai Gon, ket hop cafe va chup anh hoang hon.", 220000, "Cafe/check-in", "https://en.wikivoyage.org/wiki/Ho_Chi_Minh_City", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Moc Chau Tea Hill Photo Ride", "Moc Chau", "Di doi che Moc Chau, chup anh mua hoa va ghe quan sua chua dia phuong.", 300000, "Viewpoint", "https://en.wikivoyage.org/wiki/Moc_Chau", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Quy Nhon Eo Gio Coastal Walk", "Quy Nhon", "Cung duong bien Eo Gio, Ky Co va cac diem chup anh nhe trong nua ngay.", 420000, "Viewpoint", "https://en.wikivoyage.org/wiki/Quy_Nhon", "https://images.unsplash.com/photo-1513553404607-988bf2703777?auto=format&fit=crop&w=1200&q=80"),
            ("Con Dao Dam Trau Beach Chill", "Con Dao", "Buoi chieu bien Dam Trau, cafe nho va ngam may bay/hoang hon neu dung gio.", 260000, "Viewpoint", "https://en.wikivoyage.org/wiki/Con_Dao", "https://images.unsplash.com/photo-1513415564515-763d91423bdd?auto=format&fit=crop&w=1200&q=80"),
            ("Can Tho Night Market Snack Walk", "Can Tho", "Lich trinh an vat cho dem Can Tho, ben Ninh Kieu va cafe ven song.", 240000, "Local experience", "https://en.wikivoyage.org/wiki/Can_Tho", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Nha Trang Hon Chong Sunset Stop", "Nha Trang", "Diem ngam bien Hon Chong, chup anh da bien va ket hop cafe ven bien.", 180000, "Viewpoint", "https://en.wikivoyage.org/wiki/Nha_Trang", "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=1200&q=80"),
        ]
        activities = []
        for title, city, text, price, category_name, source, image in rows:
            category = categories[category_name]
            activity, _ = Activity.objects.update_or_create(
                slug=slugify(f"{title}-{city}"),
                defaults={
                    "title": title,
                    "category": category,
                    "description": f"{text}\n\n{SOURCE_NOTE.format(source=source)}",
                    "short_description": text,
                    "city": city,
                    "country": "Vietnam",
                    "address": city,
                    "price_adult": Decimal(price),
                    "price_child": (Decimal(price) * Decimal("0.7")).quantize(Decimal("1")),
                    "duration_hours": Decimal("2.5"),
                    "difficulty": "easy",
                    "max_participants": 12,
                    "min_age": 0,
                    "image_url": image,
                    "includes_equipment": False,
                    "includes_transport": True,
                    "includes_meals": category_name == "Cafe/check-in",
                    "includes_guide": True,
                    "is_active": True,
                    "featured": True,
                },
            )
            ActivityImage.objects.update_or_create(
                activity=activity,
                is_primary=True,
                defaults={
                    "external_url": image,
                    "caption": title,
                    "alt_text": title,
                    "display_order": 0,
                },
            )
            activities.append(activity)
        return activities

    def ensure_activity_categories(self):
        rows = {
            "Cafe/check-in": ("Cafe dep, rooftop, goc chup anh duoc gioi tre yeu thich", "fas fa-mug-hot"),
            "Viewpoint": ("Diem ngam canh, san may, hoang hon, binh minh", "fas fa-camera-retro"),
            "Local experience": ("Trai nghiem dia phuong ngan, de chen vao lich trinh", "fas fa-route"),
        }
        categories = {}
        for name, (description, icon) in rows.items():
            category, _ = ActivityCategory.objects.update_or_create(
                name=name,
                defaults={"description": description, "icon": icon},
            )
            categories[name] = category
        return categories
