from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from activities.models import Activity, ActivityCategory, ActivityImage
from packages.models import PackageComponent, PackageImage, TravelPackage


SOURCE_NOTE = "Du lieu tham khao tu nguon cong khai: {source}"


class Command(BaseCommand):
    help = "Seed Vietnam attractions, amusement parks, tourist areas and tours from public web references."

    def handle(self, *args, **options):
        with transaction.atomic():
            categories = self.create_categories()
            activities = self.create_activities(categories)
            packages = self.create_packages(activities)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded/updated {len(activities)} activities and {len(packages)} travel packages."
        ))

    def create_categories(self):
        data = {
            "Check-in noi bat": ("Diem chup anh, bieu tuong thanh pho, canh quan dac trung", "fas fa-camera"),
            "Khu vui choi": ("Cong vien chu de, cap treo, show dien, thuy cung", "fas fa-ticket-alt"),
            "Di san & van hoa": ("Di tich, bao tang, pho co, lang nghe", "fas fa-landmark"),
            "Thien nhien": ("Vinh, hang dong, nui, ruong bac thang, bien dao", "fas fa-mountain"),
            "Am thuc & trai nghiem dia phuong": ("Tour an uong, cho dem, cafe, lop nau an", "fas fa-utensils"),
        }
        categories = {}
        for name, (description, icon) in data.items():
            category, _ = ActivityCategory.objects.update_or_create(
                name=name,
                defaults={"description": description, "icon": icon},
            )
            categories[name] = category
        return categories

    def create_activities(self, categories):
        rows = [
            ("Hoan Kiem Lake & Old Quarter Walk", "Ha Noi", "Di san & van hoa", "Pho co Ha Noi, Ho Hoan Kiem, cau The Huc va khong gian am thuc duong pho.", 180000, 3, "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80"),
            ("Hoa Lo Prison Museum", "Ha Noi", "Di san & van hoa", "Bao tang lich su giua trung tam Ha Noi, phu hop lich trinh nua ngay.", 120000, 1.5, "https://en.wikivoyage.org/wiki/Hanoi/Hoan_Kiem", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("Temple of Literature", "Ha Noi", "Di san & van hoa", "Van Mieu - Quoc Tu Giam, diem tham quan van hoa giao duc lau doi cua Ha Noi.", 100000, 1.5, "https://en.wikivoyage.org/wiki/Hanoi", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("Ha Long Bay Day Cruise", "Ha Long", "Thien nhien", "Du thuyen tham vinh, hang dong va cac dao da voi tren Vinh Ha Long.", 1250000, 6, "https://vietnamtourism.gov.vn/en/post/16441", "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80"),
            ("Sun World Ha Long Complex", "Ha Long", "Khu vui choi", "To hop vui choi Bai Chay va Ba Deo voi cap treo, cong vien giai tri va view vinh.", 650000, 5, "https://halong.sunworld.vn/en", "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1200&q=80"),
            ("Sa Pa Trekking Lao Chai - Ta Van", "Sa Pa", "Thien nhien", "Trekking ruong bac thang, ban lang va van hoa dan toc thieu so quanh Sa Pa.", 780000, 6, "https://www.vietnam.travel/places-to-go/northern-vietnam/sapa", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Fansipan Cable Car Experience", "Sa Pa", "Check-in noi bat", "Trai nghiem cap treo len khu vuc dinh Fansipan va ngam nui rung Hoang Lien Son.", 950000, 4, "https://www.vietnam.travel/places-to-go/northern-vietnam/sapa", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80"),
            ("Trang An Boat Tour", "Ninh Binh", "Thien nhien", "Ngoi thuyen qua hang dong, nui da voi va canh quan di san Trang An.", 350000, 3, "https://en.wikipedia.org/wiki/Tr%C3%A0ng_An_Scenic_Landscape_Complex", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
            ("Tam Coc - Bich Dong Cycling", "Ninh Binh", "Thien nhien", "Dap xe giua lang que, dong lua va chua Bich Dong gan khu Tam Coc.", 420000, 4, "https://en.wikivoyage.org/wiki/Ninh_Binh", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
            ("Hue Imperial City", "Hue", "Di san & van hoa", "Tham quan Hoang thanh Hue, lang tam va cau chuyen trieu Nguyen.", 360000, 4, "https://www.vietnam.travel/places-to-go/central-vietnam/hue", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("Perfume River Dragon Boat", "Hue", "Check-in noi bat", "Di thuyen song Huong, nghe ca Hue va ngam thanh pho ve dem.", 300000, 2, "https://en.wikivoyage.org/wiki/Hue", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("Sun World Ba Na Hills", "Da Nang", "Khu vui choi", "Cong vien tren nui Chua, Cau Vang, cap treo va khu lang Phap.", 1050000, 7, "https://banahills.sunworld.vn/en", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Marble Mountains & My Khe Beach", "Da Nang", "Check-in noi bat", "Ngu Hanh Son, hang dong, chua va bai bien My Khe trong nua ngay.", 380000, 4, "https://en.wikivoyage.org/wiki/Da_Nang", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Hoi An Ancient Town Evening", "Hoi An", "Di san & van hoa", "Di bo pho co, den long, cau Nhat Ban, quan ca phe va cho dem.", 250000, 3, "https://www.vietnam.travel/things-to-do/the-best-ways-to-explore-the-ancient-town-of-hoi-an", "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80"),
            ("Hoi An Basket Boat & Coconut Forest", "Hoi An", "Am thuc & trai nghiem dia phuong", "Cheo thuyen thung, xem quang chai va thu mon dia phuong Cam Thanh.", 420000, 3, "https://www.vietnam.travel/things-to-do/the-best-ways-to-explore-the-ancient-town-of-hoi-an", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("My Son Sanctuary Half Day", "Hoi An", "Di san & van hoa", "Khu den thap Cham Pa gan Hoi An, phu hop lich trinh van hoa nua ngay.", 520000, 4, "https://en.wikivoyage.org/wiki/Hoi_An", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("VinWonders Nha Trang", "Nha Trang", "Khu vui choi", "Cong vien giai tri tren dao Hon Tre voi cap treo, thuy cung va show dien.", 950000, 7, "https://vinwonders.com/en/vinwonders-nha-trang/", "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=1200&q=80"),
            ("Nha Trang Island Hopping", "Nha Trang", "Thien nhien", "Tour dao, tam bien, lan ngam san ho va bua trua hai san.", 780000, 6, "https://en.wikivoyage.org/wiki/Nha_Trang", "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=1200&q=80"),
            ("Da Lat Tuyen Lam Lake & Clay Tunnel", "Da Lat", "Check-in noi bat", "Ho Tuyen Lam, duong ham dat set, rung thong va cac diem chup anh noi bat.", 460000, 5, "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Da Lat Coffee & Night Market", "Da Lat", "Am thuc & trai nghiem dia phuong", "Thu ca phe dia phuong, banh trang nuong va cho dem Da Lat.", 260000, 3, "https://en.wikivoyage.org/wiki/Da_Lat", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80"),
            ("Cu Chi Tunnels Experience", "TP. Ho Chi Minh", "Di san & van hoa", "Tham quan mang duong ham Cu Chi va tim hieu lich su chien tranh.", 520000, 5, "https://en.wikipedia.org/wiki/C%E1%BB%A7_Chi_tunnels", "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80"),
            ("Saigon Food by Night", "TP. Ho Chi Minh", "Am thuc & trai nghiem dia phuong", "Thu mon an duong pho, cafe va cac quan dia phuong ve dem.", 650000, 4, "https://en.wikivoyage.org/wiki/Ho_Chi_Minh_City", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("Mekong Delta Floating Market", "Can Tho", "Am thuc & trai nghiem dia phuong", "Cho noi Cai Rang, xuong mien, vuon trai cay va kenh rach mien Tay.", 820000, 6, "https://en.wikivoyage.org/wiki/Can_Tho", "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80"),
            ("VinWonders Phu Quoc", "Phu Quoc", "Khu vui choi", "Cong vien chu de lon tai Bac dao Phu Quoc voi show dien va khu tro choi.", 1050000, 7, "https://vinwonders.com/en/vinwonders-phu-quoc/", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Phu Quoc Island South Tour", "Phu Quoc", "Thien nhien", "Hon Thom, bai Sao, cap treo va cac diem bien dao phia Nam.", 890000, 7, "https://en.wikivoyage.org/wiki/Phu_Quoc", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"),
            ("Phong Nha Cave Boat Trip", "Phong Nha", "Thien nhien", "Ngoi thuyen vao dong Phong Nha trong vung Phong Nha - Ke Bang.", 620000, 4, "https://en.wikipedia.org/wiki/Phong_Nha%E2%80%93K%E1%BA%BB_B%C3%A0ng_National_Park", "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80"),
        ]
        activities = []
        for title, city, category_name, text, price, hours, source, image in rows:
            slug = slugify(f"{title}-{city}")
            description = f"{text}\n\n{SOURCE_NOTE.format(source=source)}"
            activity, _ = Activity.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": categories[category_name],
                    "description": description,
                    "short_description": text[:500],
                    "city": city,
                    "country": "Vietnam",
                    "address": city,
                    "price_adult": Decimal(price),
                    "price_child": Decimal(price) * Decimal("0.7"),
                    "duration_hours": Decimal(str(hours)),
                    "difficulty": "easy",
                    "max_participants": 20,
                    "min_age": 0,
                    "image_url": image,
                    "includes_equipment": category_name in {"Khu vui choi", "Thien nhien"},
                    "includes_transport": True,
                    "includes_meals": category_name == "Am thuc & trai nghiem dia phuong",
                    "includes_guide": True,
                    "is_active": True,
                    "featured": category_name in {"Khu vui choi", "Thien nhien"},
                },
            )
            ActivityImage.objects.update_or_create(
                activity=activity,
                is_primary=True,
                defaults={"external_url": image, "caption": title, "alt_text": title, "display_order": 0},
            )
            activities.append(activity)
        return activities

    def create_packages(self, activities):
        activity_by_city = {}
        for activity in activities:
            activity_by_city.setdefault(activity.city, []).append(activity)

        rows = [
            ("Ha Noi - Ha Long - Ninh Binh Classic", "cultural", "Ha Noi", 5, 4, 8900000, ["Ha Noi", "Ha Long", "Ninh Binh"], "https://vietnamtourism.gov.vn/en/post/16441"),
            ("Central Heritage: Hue - Da Nang - Hoi An", "family", "Da Nang", 4, 3, 7600000, ["Hue", "Da Nang", "Hoi An"], "https://www.vietnam.travel/things-to-do/the-best-ways-to-explore-the-ancient-town-of-hoi-an"),
            ("Da Nang Theme Park & Beach Break", "family", "Da Nang", 3, 2, 5200000, ["Da Nang", "Hoi An"], "https://banahills.sunworld.vn/en"),
            ("Sa Pa Trekking & Fansipan", "adventure", "Sa Pa", 3, 2, 4800000, ["Sa Pa"], "https://www.vietnam.travel/places-to-go/northern-vietnam/sapa"),
            ("Nha Trang Island & VinWonders", "family", "Nha Trang", 3, 2, 5900000, ["Nha Trang"], "https://vinwonders.com/en/vinwonders-nha-trang/"),
            ("Da Lat Chill Food & Nature", "budget", "Da Lat", 3, 2, 3900000, ["Da Lat"], "https://en.wikivoyage.org/wiki/Da_Lat"),
            ("Saigon - Cu Chi - Mekong Delta", "cultural", "TP. Ho Chi Minh", 4, 3, 6800000, ["TP. Ho Chi Minh", "Can Tho"], "https://en.wikipedia.org/wiki/C%E1%BB%A7_Chi_tunnels"),
            ("Phu Quoc Family Fun", "luxury", "Phu Quoc", 4, 3, 8200000, ["Phu Quoc"], "https://vinwonders.com/en/vinwonders-phu-quoc/"),
            ("Phong Nha Cave Adventure", "adventure", "Phong Nha", 3, 2, 6200000, ["Phong Nha"], "https://en.wikipedia.org/wiki/Phong_Nha%E2%80%93K%E1%BA%BB_B%C3%A0ng_National_Park"),
            ("Vietnam Highlights 9 Days", "cultural", "Ha Noi", 9, 8, 18500000, ["Ha Noi", "Ha Long", "Ninh Binh", "Hue", "Da Nang", "Hoi An", "TP. Ho Chi Minh"], "https://en.wikivoyage.org/wiki/Vietnam"),
        ]
        packages = []
        for title, package_type, city, days, nights, price, cities, source in rows:
            slug = slugify(title)
            description = (
                f"Tour goi y {days} ngay {nights} dem ket hop cac diem tham quan, khu vui choi, am thuc va di chuyen dia phuong. "
                f"Lich trinh phu hop khach tre, gia dinh hoac nhom ban muon co san ke hoach.\n\n"
                f"{SOURCE_NOTE.format(source=source)}"
            )
            package, _ = TravelPackage.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "package_type": package_type,
                    "description": description,
                    "short_description": f"Tour {days} ngay qua {', '.join(cities)} voi lich trinh an choi nghi day du.",
                    "destination_city": city,
                    "destination_country": "Vietnam",
                    "duration_days": days,
                    "duration_nights": nights,
                    "base_price_per_person": Decimal(price),
                    "child_price": Decimal(price) * Decimal("0.75"),
                    "single_supplement": Decimal("900000"),
                    "includes_flight": False,
                    "includes_hotel": True,
                    "includes_meals": True,
                    "includes_activities": True,
                    "includes_transport": True,
                    "includes_insurance": False,
                    "min_participants": 2,
                    "max_participants": 18,
                    "image_url": self.package_image(city),
                    "is_active": True,
                    "featured": days >= 4,
                },
            )
            PackageImage.objects.update_or_create(
                package=package,
                is_primary=True,
                defaults={"external_url": self.package_image(city), "caption": title, "alt_text": title, "display_order": 0},
            )
            package.components.all().delete()
            day = 1
            component_order = 0
            for component_city in cities:
                for activity in activity_by_city.get(component_city, [])[:2]:
                    component_order += 1
                    PackageComponent.objects.create(
                        package=package,
                        component_type="activity",
                        title=activity.title,
                        description=activity.short_description,
                        activity=activity,
                        day_number=min(day, days),
                        duration=f"{activity.duration_hours} gio",
                        is_included=True,
                    )
                day += 1
            packages.append(package)
        return packages

    def package_image(self, city):
        images = {
            "Ha Noi": "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?auto=format&fit=crop&w=1200&q=80",
            "Da Nang": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=80",
            "Sa Pa": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            "Nha Trang": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?auto=format&fit=crop&w=1200&q=80",
            "Da Lat": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
            "TP. Ho Chi Minh": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
            "Phu Quoc": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
            "Phong Nha": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1200&q=80",
        }
        return images.get(city, images["Ha Noi"])
