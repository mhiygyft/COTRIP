from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from activities.models import Activity, ActivityCategory
from flights.models import Aircraft, Airline, Airport, Country as FlightCountry, Flight, Route
from hotels.models import Amenity, City, Country as HotelCountry, Hotel, RoomAvailability, RoomType
from packages.models import TravelPackage


class Command(BaseCommand):
    help = "Populate Vietnam-focused sample data for the travel website."

    def handle(self, *args, **options):
        self.create_hotels()
        self.create_flights()
        self.create_activities()
        self.create_packages()
        self.stdout.write(self.style.SUCCESS("Vietnam travel sample data is ready."))

    def create_hotels(self):
        vietnam, _ = HotelCountry.objects.get_or_create(
            code="VN",
            defaults={"name": "Viet Nam", "is_popular": True},
        )

        city_data = [
            ("Ha Noi", "Pho co, ho Hoan Kiem, am thuc via he va van hoa nghin nam."),
            ("Da Nang", "Thanh pho bien nang dong gan Hoi An, Hue va ban dao Son Tra."),
            ("Hoi An", "Pho co den long, nha co, lang nghe va am thuc mien Trung."),
            ("Phu Quoc", "Dao ngoc voi bai bien, resort va trai nghiem bien dao."),
            ("Sa Pa", "Nui rung Tay Bac, ruong bac thang va ban lang dan toc."),
            ("Hue", "Co do voi dai noi, lang tam, song Huong va am thuc cung dinh."),
            ("Nha Trang", "Thanh pho bien voi dao, san ho, tam bun va hai san tuoi."),
            ("Da Lat", "Cao nguyen mat lanh voi thac nuoc, doi thong va quan ca phe view nui."),
            ("Quy Nhon", "Bien xanh, Eo Gio, Ky Co va khong khi nghi duong yen tinh."),
            ("Can Tho", "Trung tam mien Tay voi cho noi, vuon trai cay va song nuoc."),
            ("Ha Long", "Vinh di san, du thuyen, hang dong va cac lang chai ven bien."),
            ("Ninh Binh", "Trang An, Tam Coc, chua Bai Dinh va canh quan nui da voi."),
            ("Ha Giang", "Cao nguyen da, deo Ma Pi Leng va cung duong vong cung Dong Van."),
            ("Mui Ne", "Doi cat, bien, lang chai va cac resort nghi duong ven bien."),
            ("Con Dao", "Bien hoang so, lich su, lan bien va nghi duong yen tinh."),
        ]

        cities = {}
        for name, description in city_data:
            city, _ = City.objects.get_or_create(
                name=name,
                country=vietnam,
                defaults={"is_popular": True, "description": description},
            )
            cities[name] = city

        amenities = []
        for name, category, icon in [
            ("WiFi mien phi", "internet", "bi bi-wifi"),
            ("Ho boi", "wellness", "bi bi-water"),
            ("Gan trung tam", "transportation", "bi bi-geo-alt"),
            ("Bua sang dia phuong", "food_drink", "bi bi-cup-hot"),
            ("Don tien san bay", "transportation", "bi bi-car-front"),
            ("Nha hang", "food_drink", "bi bi-shop"),
            ("Spa", "wellness", "bi bi-heart-pulse"),
            ("Phong gia dinh", "family", "bi bi-people"),
            ("View bien", "view", "bi bi-sunrise"),
            ("View nui", "view", "bi bi-mountains"),
            ("Cho dau xe", "transportation", "bi bi-p-square"),
            ("Le tan 24 gio", "service", "bi bi-clock"),
        ]:
            amenity, _ = Amenity.objects.get_or_create(
                name=name,
                defaults={"category": category, "icon": icon, "is_popular": True},
            )
            amenities.append(amenity)

        hotels = [
            ("La Siesta Classic Ha Noi", "Ha Noi", "Khach san boutique gan pho co, phu hop kham pha am thuc va di san.", 85),
            ("My Khe Beach Retreat", "Da Nang", "Luu tru gan bien My Khe, thuan tien di Hoi An va Son Tra.", 95),
            ("Hoi An Lantern Riverside", "Hoi An", "Khach san ven song, gan pho co va cac lop nau an dia phuong.", 78),
            ("Phu Quoc Sunset Resort", "Phu Quoc", "Resort nghi duong gan bien, phu hop ky nghi dai ngay.", 120),
            ("Sa Pa Mountain Lodge", "Sa Pa", "Lodge nhin ra ruong bac thang, gan cac tuyen trekking ban lang.", 65),
            ("Hoan Kiem Boutique Stay", "Ha Noi", "Luu tru gan ho Hoan Kiem, thuan tien di bo pho co.", 58),
            ("An Bang Garden Villa", "Hoi An", "Villa yen tinh gan bien An Bang va pho co Hoi An.", 88),
            ("Phu Quoc Family Resort", "Phu Quoc", "Resort nhieu hoat dong cho gia dinh, gan bai Dai.", 105),
            ("Sa Pa Cloud View", "Sa Pa", "Khach san view nui, thuan tien di trekking va cho dem.", 55),
            ("Da Nang Riverfront Hotel", "Da Nang", "Khach san ven song Han, gan cau Rong va bai bien My Khe.", 82),
            ("Hue Imperial Garden Hotel", "Hue", "Khach san gan dai noi Hue, phu hop tham quan di san va am thuc co do.", 76),
            ("Nha Trang Coral Bay Hotel", "Nha Trang", "Luu tru gan bien Tran Phu, thuan tien di tour dao va tam bun.", 92),
            ("Da Lat Pine Hill Retreat", "Da Lat", "Retreat tren doi thong, phu hop nghi duong va kham pha thanh pho ngan hoa.", 70),
            ("Quy Nhon Blue Coast", "Quy Nhon", "Khach san gan bien, de di Eo Gio, Ky Co va cac quan hai san dia phuong.", 68),
            ("Can Tho Riverside Stay", "Can Tho", "Khach san ven song Hau, thuan tien di cho noi Cai Rang sang som.", 62),
            ("Ha Long Bay View Hotel", "Ha Long", "Luu tru gan ben du thuyen, phu hop hanh trinh tham vinh Ha Long.", 88),
            ("Ninh Binh Limestone Lodge", "Ninh Binh", "Lodge gan Trang An va Tam Coc, nhin ra nui da voi va dong lua.", 64),
            ("Ha Giang Loop Inn", "Ha Giang", "Diem dung chan cho cung duong Ha Giang, co dich vu thue xe va huong dan vien.", 52),
            ("Mui Ne Sand Dune Resort", "Mui Ne", "Resort ven bien gan doi cat bay, phu hop nghi duong va the thao bien.", 84),
            ("Con Dao Ocean Hideaway", "Con Dao", "Khach san yen tinh gan bien, phu hop nghi duong va lan ngam san ho.", 118),
        ]

        for name, city_name, description, price in hotels:
            hotel, _ = Hotel.objects.get_or_create(
                name=name,
                city=cities[city_name],
                defaults={
                    "address": city_name,
                    "description": description,
                    "star_rating": 4,
                    "price_from": Decimal(str(price)),
                    "currency": "VND",
                    "is_active": True,
                    "is_featured": True,
                    "is_verified": True,
                    "average_rating": Decimal("9.10"),
                    "total_reviews": 128,
                    "total_rooms": 42,
                },
            )
            hotel.total_rooms = max(hotel.total_rooms, 80)
            hotel.is_active = True
            hotel.is_featured = True
            hotel.save()
            hotel.amenities.set(amenities)
            self.create_room_inventory(hotel, amenities)

    def create_room_inventory(self, hotel, amenities):
        room_specs = [
            ("Standard Viet Nam Room", "Phong tieu chuan day du tien nghi cho 2 khach.", 28, 2, "queen", 32, hotel.price_from),
            ("Deluxe City View", "Phong rong hon voi huong nhin thanh pho va bua sang dia phuong.", 36, 3, "king", 26, hotel.price_from + Decimal("28")),
            ("Family Suite", "Suite gia dinh co khong gian sinh hoat rieng va suc chua lon.", 52, 4, "queen", 18, hotel.price_from + Decimal("65")),
        ]
        today = timezone.localdate()

        for name, description, size_sqm, occupancy, bed_type, total_rooms, price in room_specs:
            room_type, _ = RoomType.objects.get_or_create(
                hotel=hotel,
                name=name,
                defaults={
                    "description": description,
                    "size_sqm": size_sqm,
                    "max_occupancy": occupancy,
                    "max_adults": occupancy,
                    "max_children": max(0, occupancy - 2),
                    "bed_type": bed_type,
                    "number_of_beds": 2 if occupancy > 2 else 1,
                    "base_price": price,
                    "is_refundable": True,
                    "total_rooms": total_rooms,
                    "is_active": True,
                },
            )
            room_type.description = description
            room_type.base_price = price
            room_type.total_rooms = max(room_type.total_rooms, total_rooms)
            room_type.is_active = True
            room_type.save()
            room_type.amenities.set(amenities)

            for day_offset in range(0, 90):
                stay_date = today + timedelta(days=day_offset)
                is_weekend = stay_date.weekday() >= 5
                multiplier = Decimal("1.15") if is_weekend else Decimal("1.00")
                availability, _ = RoomAvailability.objects.get_or_create(
                    room_type=room_type,
                    date=stay_date,
                    defaults={
                        "available_rooms": max(8, int(room_type.total_rooms * Decimal("0.75"))),
                        "price": price * multiplier,
                        "is_weekend": is_weekend,
                        "demand_multiplier": multiplier,
                    },
                )
                availability.available_rooms = max(availability.available_rooms, 8)
                availability.price = price * multiplier
                availability.is_weekend = is_weekend
                availability.demand_multiplier = multiplier
                availability.save()

    def create_flights(self):
        vietnam, _ = FlightCountry.objects.get_or_create(
            iso_code="VN",
            defaults={"name": "Viet Nam", "code": "VNM", "currency": "VND", "timezone": "Asia/Ho_Chi_Minh"},
        )

        airport_data = [
            ("Noi Bai International Airport", "HAN", "VVNB", "Ha Noi"),
            ("Da Nang International Airport", "DAD", "VVDN", "Da Nang"),
            ("Tan Son Nhat International Airport", "SGN", "VVTS", "TP. Ho Chi Minh"),
            ("Phu Quoc International Airport", "PQC", "VVPQ", "Phu Quoc"),
            ("Cam Ranh International Airport", "CXR", "VVCR", "Nha Trang"),
            ("Van Don International Airport", "VDO", "VVVD", "Quang Ninh"),
            ("Cat Bi International Airport", "HPH", "VVCI", "Hai Phong"),
            ("Lien Khuong Airport", "DLI", "VVDL", "Da Lat"),
            ("Phu Bai International Airport", "HUI", "VVPB", "Hue"),
        ]
        airports = {}
        for name, iata, icao, city in airport_data:
            airport, _ = Airport.objects.get_or_create(
                iata_code=iata,
                defaults={
                    "name": name,
                    "icao_code": icao,
                    "city": city,
                    "country": vietnam,
                    "timezone": "Asia/Ho_Chi_Minh",
                    "is_active": True,
                    "is_international": True,
                    "is_popular": True,
                },
            )
            airports[iata] = airport

        airline_specs = [
            ("Vietnam Airlines", "VN", "HVN", False, Decimal("4.60"), 854),
            ("Vietjet Air", "VJ", "VJC", True, Decimal("4.10"), 621),
            ("Bamboo Airways", "QH", "BAV", False, Decimal("4.30"), 438),
        ]
        airlines = []
        for name, iata, icao, is_low_cost, rating, reviews in airline_specs:
            airline, _ = Airline.objects.get_or_create(
                iata_code=iata,
                defaults={
                    "name": name,
                    "icao_code": icao,
                    "country": vietnam,
                    "is_active": True,
                    "is_low_cost": is_low_cost,
                    "average_rating": rating,
                    "total_reviews": reviews,
                },
            )
            airline.is_active = True
            airline.average_rating = rating
            airline.total_reviews = max(airline.total_reviews, reviews)
            airline.save()
            airlines.append(airline)
        aircraft, _ = Aircraft.objects.get_or_create(
            manufacturer="Airbus",
            model="A321",
            variant="neo",
            defaults={
                "total_seats": 203,
                "economy_seats": 185,
                "premium_economy_seats": 12,
                "business_seats": 6,
                "first_class_seats": 0,
                "is_active": True,
            },
        )

        route_specs = [
            ("HAN", "DAD", 606, 80, 78),
            ("DAD", "HAN", 606, 80, 78),
            ("HAN", "SGN", 1160, 130, 110),
            ("SGN", "HAN", 1160, 130, 110),
            ("SGN", "PQC", 300, 60, 58),
            ("PQC", "SGN", 300, 60, 58),
            ("SGN", "CXR", 310, 65, 62),
            ("CXR", "SGN", 310, 65, 62),
            ("DAD", "PQC", 795, 105, 95),
            ("PQC", "DAD", 795, 105, 95),
            ("HAN", "CXR", 1080, 120, 105),
            ("CXR", "HAN", 1080, 120, 105),
            ("DAD", "CXR", 520, 80, 72),
            ("CXR", "DAD", 520, 80, 72),
        ]
        base_date = timezone.localdate()
        flight_index = 1
        for route_index, (origin, destination, distance, duration, price) in enumerate(route_specs, start=1):
            route, _ = Route.objects.get_or_create(
                origin=airports[origin],
                destination=airports[destination],
                defaults={
                    "distance_km": distance,
                    "typical_duration_minutes": duration,
                    "is_popular": True,
                    "is_domestic": True,
                    "base_price": Decimal(str(price)),
                },
            )
            for day_offset in range(1, 31):
                for hour in (7, 13, 19):
                    departure = timezone.make_aware(
                        datetime.combine(
                            base_date + timedelta(days=day_offset),
                            time(hour=hour, minute=(route_index * 5) % 60),
                        )
                    )
                    for airline_index, airline in enumerate(airlines):
                        price_adjustment = Decimal(str((hour - 7) // 6 * 8 + airline_index * 6))
                        flight, _ = Flight.objects.get_or_create(
                            airline=airline,
                            flight_number=f"{1200 + flight_index}",
                            departure_time=departure,
                            defaults={
                                "aircraft": aircraft,
                                "origin": airports[origin],
                                "destination": airports[destination],
                                "route": route,
                                "arrival_time": departure + timedelta(minutes=duration),
                                "duration_minutes": duration,
                                "distance_km": distance,
                                "stops": 0,
                                "economy_price": Decimal(str(price)) + price_adjustment,
                                "premium_economy_price": Decimal(str(price + 35)) + price_adjustment,
                                "business_price": Decimal(str(price + 95)) + price_adjustment,
                                "first_class_price": None,
                                "economy_available": 160,
                                "premium_economy_available": 18,
                                "business_available": 8,
                                "first_class_available": 0,
                                "is_active": True,
                            },
                        )
                        flight.economy_available = max(flight.economy_available, 140)
                        flight.premium_economy_available = max(flight.premium_economy_available, 12)
                        flight.business_available = max(flight.business_available, 6)
                        flight.first_class_available = 0
                        flight.is_active = True
                        flight.save()
                        flight_index += 1

    def create_activities(self):
        categories = {}
        for name, icon in [
            ("Am thuc", "bi bi-cup-hot"),
            ("Thien nhien", "bi bi-tree"),
            ("Van hoa", "bi bi-bank"),
            ("Bien dao", "bi bi-water"),
            ("Phieu luu", "bi bi-compass"),
            ("Gia dinh", "bi bi-people"),
            ("Nghi duong", "bi bi-suitcase"),
        ]:
            category, _ = ActivityCategory.objects.get_or_create(name=name, defaults={"icon": icon})
            categories[name] = category

        activity_data = [
            ("Lop nau an Hoi An", "Am thuc", "Hoi An", "Hoc nau mon Viet sau khi di cho dia phuong.", 32),
            ("Trekking ban lang Sa Pa", "Thien nhien", "Sa Pa", "Di bo qua ruong bac thang va ban lang Tay Bac.", 45),
            ("Tour di san Hue", "Van hoa", "Hue", "Kham pha dai noi, lang tam va am thuc co do.", 38),
            ("Du thuyen Ha Long trong ngay", "Thien nhien", "Ha Long", "Di thuyen qua vinh, hang dong va lang chai.", 58),
            ("Food tour pho co Ha Noi", "Am thuc", "Ha Noi", "Thuong thuc pho, bun cha, ca phe trung va cac mon via he.", 28),
            ("Lan ngam san ho Phu Quoc", "Thien nhien", "Phu Quoc", "Kham pha dao nho, san ho va bai bien phia nam dao.", 52),
            ("Dia dao Cu Chi va Sai Gon", "Van hoa", "TP. Ho Chi Minh", "Tim hieu lich su dia dao va nhung diem noi bat Sai Gon.", 36),
            ("Mot ngay Da Lat", "Thien nhien", "Da Lat", "Tham quan thac nuoc, doi che, vuon hoa va quan ca phe view nui.", 42),
            ("Du thuyen hoang hon Nha Trang", "Bien dao", "Nha Trang", "Di thuyen ngam hoang hon, thuong thuc hai san va ngam thanh pho bien.", 49),
            ("Kham pha Eo Gio Ky Co", "Bien dao", "Quy Nhon", "Tham quan Eo Gio, Ky Co, lan ngam san ho va an trua hai san.", 46),
            ("Cho noi Cai Rang sang som", "Van hoa", "Can Tho", "Di thuyen lenh denh cho noi, thu trai cay va am thuc mien Tay.", 30),
            ("Trang An va Tam Coc trong ngay", "Thien nhien", "Ninh Binh", "Di thuyen qua hang dong, tham chua va ngam canh nui da voi.", 40),
            ("Ha Giang Loop hai ngay", "Phieu luu", "Ha Giang", "Chinh phuc cac cung deo dep, lang ban va cao nguyen da Dong Van.", 88),
            ("Sandboarding Mui Ne", "Phieu luu", "Mui Ne", "Trai nghiem truot cat, xe dia hinh va lang chai Mui Ne.", 34),
            ("Tour lich su Con Dao", "Van hoa", "Con Dao", "Tham quan cac di tich lich su, nghia trang va bai bien yen tinh.", 44),
            ("Tam bun khoang Nha Trang", "Nghi duong", "Nha Trang", "Thu gian voi tam bun khoang, spa va dich vu cham soc suc khoe.", 27),
            ("Lam nong trai Da Lat", "Gia dinh", "Da Lat", "Hai dau, tham vuon rau, choi voi thu cung va dung bua trua dia phuong.", 35),
            ("Di bo pho co va ca phe Ha Noi", "Am thuc", "Ha Noi", "Kham pha cac hem pho co, ca phe dac san va mon an duong pho.", 24),
        ]
        for title, category, city, description, price in activity_data:
            activity, _ = Activity.objects.get_or_create(
                title=title,
                defaults={
                    "slug": title.lower().replace(" ", "-"),
                    "category": categories[category],
                    "description": description,
                    "short_description": description,
                    "city": city,
                    "country": "Viet Nam",
                    "address": city,
                    "price_adult": Decimal(str(price)),
                    "duration_hours": Decimal("4.0"),
                    "difficulty": "easy",
                    "max_participants": 12,
                    "featured": True,
                    "is_active": True,
                },
            )
            activity.max_participants = max(activity.max_participants, 40)
            activity.featured = True
            activity.is_active = True
            activity.save()

    def create_packages(self):
        package_data = [
            ("Ha Noi - Ha Long - Ninh Binh 4N3D", "cultural", "Ha Noi", "Viet Nam", 4, 3, 320),
            ("Da Nang - Hoi An - Hue 5N4D", "family", "Da Nang", "Viet Nam", 5, 4, 410),
            ("TP.HCM - Mekong - Phu Quoc 6N5D", "luxury", "TP. Ho Chi Minh", "Viet Nam", 6, 5, 560),
            ("Sa Pa - Ha Giang 5N4D", "adventure", "Sa Pa", "Viet Nam", 5, 4, 480),
            ("Nha Trang - Da Lat 5N4D", "family", "Nha Trang", "Viet Nam", 5, 4, 430),
            ("Phu Quoc Resort 4N3D", "luxury", "Phu Quoc", "Viet Nam", 4, 3, 520),
            ("Hue - Quang Binh 4N3D", "cultural", "Hue", "Viet Nam", 4, 3, 360),
            ("Quy Nhon - Phu Yen 4N3D", "family", "Quy Nhon", "Viet Nam", 4, 3, 390),
            ("Can Tho - Chau Doc 3N2D", "cultural", "Can Tho", "Viet Nam", 3, 2, 260),
            ("Ha Long - Cat Ba 4N3D", "family", "Ha Long", "Viet Nam", 4, 3, 420),
            ("Ninh Binh - Pu Luong 4N3D", "adventure", "Ninh Binh", "Viet Nam", 4, 3, 370),
            ("Mui Ne - Da Lat 5N4D", "family", "Mui Ne", "Viet Nam", 5, 4, 440),
            ("Con Dao nghi duong 4N3D", "luxury", "Con Dao", "Viet Nam", 4, 3, 610),
            ("Ha Giang Loop 4N3D", "adventure", "Ha Giang", "Viet Nam", 4, 3, 390),
        ]
        for title, package_type, city, country, days, nights, price in package_data:
            package, _ = TravelPackage.objects.get_or_create(
                slug=title.lower().replace(" ", "-").replace(".", "").replace("đ", "d"),
                defaults={
                    "title": title,
                    "package_type": package_type,
                    "description": f"Tour {title} voi lich trinh can bang giua tham quan, nghi ngoi va am thuc dia phuong.",
                    "short_description": "Lich trinh du lich Viet Nam tron goi, phu hop khach gia dinh va nhom ban.",
                    "destination_city": city,
                    "destination_country": country,
                    "duration_days": days,
                    "duration_nights": nights,
                    "base_price_per_person": Decimal(str(price)),
                    "includes_flight": True,
                    "includes_hotel": True,
                    "includes_meals": True,
                    "includes_activities": True,
                    "includes_transport": True,
                    "featured": True,
                    "is_active": True,
                },
            )
            package.max_participants = max(package.max_participants, 60)
            package.featured = True
            package.is_active = True
            package.save()
