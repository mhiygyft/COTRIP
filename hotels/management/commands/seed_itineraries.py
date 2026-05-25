from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand

from hotels.models import City, Country, Itinerary, ItineraryStop


class Command(BaseCommand):
    help = 'Seed sample Hanoi itineraries.'

    def handle(self, *args, **options):
        city = self.get_hanoi_city()
        image_url = city.image_source_url

        itineraries = [
            {
                'title': 'Hà Nội 3 ngày 2 đêm',
                'days': 3,
                'description': 'Lịch trình cân bằng giữa phố cổ, di sản văn hóa và ẩm thực địa phương.',
                'order': 1,
                'stops': [
                    (1, 'morning', 'Hồ Hoàn Kiếm', 'Dạo quanh hồ, thăm đền Ngọc Sơn và bắt nhịp không khí trung tâm Hà Nội.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Hoan+Kiem+Lake+Hanoi'),
                    (1, 'afternoon', 'Phố cổ Hà Nội', 'Khám phá các tuyến phố nghề, quán cà phê nhỏ và kiến trúc nhà ống đặc trưng.', 2.5, 'https://www.google.com/maps/search/?api=1&query=Hanoi+Old+Quarter'),
                    (1, 'evening', 'Chợ đêm Đồng Xuân', 'Thưởng thức món ăn đường phố và mua quà lưu niệm quanh khu chợ đêm.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Dong+Xuan+Market+Hanoi'),
                    (2, 'morning', 'Lăng Chủ tịch Hồ Chí Minh', 'Tham quan quảng trường Ba Đình, khu di tích Phủ Chủ tịch và chùa Một Cột.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Ho+Chi+Minh+Mausoleum+Hanoi'),
                    (2, 'afternoon', 'Văn Miếu - Quốc Tử Giám', 'Tìm hiểu trường đại học đầu tiên của Việt Nam và không gian kiến trúc truyền thống.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Temple+of+Literature+Hanoi'),
                    (2, 'evening', 'Tạ Hiện', 'Ghé khu phố sôi động để ăn tối nhẹ và cảm nhận nhịp sống về đêm.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Ta+Hien+Street+Hanoi'),
                    (3, 'morning', 'Bảo tàng Dân tộc học Việt Nam', 'Xem hiện vật, nhà truyền thống và câu chuyện văn hóa của các dân tộc Việt Nam.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Vietnam+Museum+of+Ethnology'),
                    (3, 'afternoon', 'Hồ Tây', 'Thư giãn bên hồ, ghé chùa Trấn Quốc và các quán ven hồ.', 2.0, 'https://www.google.com/maps/search/?api=1&query=West+Lake+Hanoi'),
                    (3, 'evening', 'Nhà hát múa rối nước Thăng Long', 'Kết thúc chuyến đi bằng suất diễn múa rối nước truyền thống gần hồ Hoàn Kiếm.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Thang+Long+Water+Puppet+Theatre'),
                ],
            },
            {
                'title': 'Hà Nội 5 ngày 4 đêm',
                'days': 5,
                'description': 'Lịch trình chậm hơn, thêm làng nghề, bảo tàng và các điểm xanh quanh thủ đô.',
                'order': 2,
                'stops': [
                    (1, 'morning', 'Hồ Hoàn Kiếm', 'Bắt đầu bằng tuyến đi bộ quanh hồ và khu phố trung tâm.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Hoan+Kiem+Lake+Hanoi'),
                    (1, 'afternoon', 'Phố cổ Hà Nội', 'Len qua Hàng Bạc, Hàng Gai, Mã Mây và các quán ăn lâu năm.', 2.5, 'https://www.google.com/maps/search/?api=1&query=Hanoi+Old+Quarter'),
                    (1, 'evening', 'Ẩm thực phố cổ', 'Thử bún chả, phở, nem rán hoặc cà phê trứng trong khu phố cổ.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Old+Quarter+Hanoi+food'),
                    (2, 'morning', 'Lăng Chủ tịch Hồ Chí Minh', 'Thăm cụm di tích Ba Đình và chùa Một Cột trong buổi sáng.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Ho+Chi+Minh+Mausoleum+Hanoi'),
                    (2, 'afternoon', 'Văn Miếu - Quốc Tử Giám', 'Dành thời gian đọc bia tiến sĩ, sân vườn và các lớp kiến trúc cổ.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Temple+of+Literature+Hanoi'),
                    (2, 'evening', 'Phố đi bộ Hồ Gươm', 'Tản bộ, xem biểu diễn đường phố và thưởng thức đồ uống quanh hồ.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Hoan+Kiem+walking+street'),
                    (3, 'morning', 'Bảo tàng Dân tộc học Việt Nam', 'Tìm hiểu đời sống, trang phục và kiến trúc của các cộng đồng dân tộc.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Vietnam+Museum+of+Ethnology'),
                    (3, 'afternoon', 'Hồ Tây và chùa Trấn Quốc', 'Đi một vòng Hồ Tây, ghé chùa Trấn Quốc và nghỉ tại quán ven hồ.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Tran+Quoc+Pagoda+Hanoi'),
                    (3, 'evening', 'Quảng An', 'Ăn tối ở khu Quảng An với nhiều lựa chọn món Việt và quốc tế.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Quang+An+Tay+Ho+Hanoi'),
                    (4, 'morning', 'Làng gốm Bát Tràng', 'Đi ngoại thành xem xưởng gốm, chợ gốm và tự tay thử làm sản phẩm.', 3.0, 'https://www.google.com/maps/search/?api=1&query=Bat+Trang+Ceramic+Village'),
                    (4, 'afternoon', 'Long Biên', 'Ghé cầu Long Biên và khu bãi giữa để chụp ảnh, ngắm sông Hồng.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Long+Bien+Bridge+Hanoi'),
                    (4, 'evening', 'Nhà hát Lớn Hà Nội', 'Dạo quanh khu phố Pháp và xem lịch biểu diễn nếu có chương trình phù hợp.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Hanoi+Opera+House'),
                    (5, 'morning', 'Hoàng thành Thăng Long', 'Khám phá di sản thế giới và các lớp dấu tích lịch sử của kinh thành xưa.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Imperial+Citadel+of+Thang+Long'),
                    (5, 'afternoon', 'Bảo tàng Mỹ thuật Việt Nam', 'Xem sưu tập tranh, điêu khắc và mỹ thuật truyền thống Việt Nam.', 1.5, 'https://www.google.com/maps/search/?api=1&query=Vietnam+Fine+Arts+Museum+Hanoi'),
                    (5, 'evening', 'Chợ Đồng Xuân', 'Mua quà, ăn nhẹ và kết thúc hành trình ở khu chợ lớn của phố cổ.', 2.0, 'https://www.google.com/maps/search/?api=1&query=Dong+Xuan+Market+Hanoi'),
                ],
            },
        ]

        created_count = 0
        for data in itineraries:
            itinerary, created = Itinerary.objects.update_or_create(
                city=city,
                title=data['title'],
                defaults={
                    'days': data['days'],
                    'description': data['description'],
                    'is_active': True,
                    'order': data['order'],
                },
            )
            itinerary.stops.all().delete()
            ItineraryStop.objects.bulk_create([
                ItineraryStop(
                    itinerary=itinerary,
                    day_number=day_number,
                    session=session,
                    place_name=place_name,
                    description=description,
                    start_time=self.default_start_time(session),
                    duration_hours=Decimal(str(duration_hours)),
                    estimated_cost=self.default_cost(session),
                    currency="VND",
                    cost_note=self.default_cost_note(session),
                    image_url=image_url,
                    google_maps_url=google_maps_url,
                    order=index,
                )
                for index, (day_number, session, place_name, description, duration_hours, google_maps_url)
                in enumerate(data['stops'], start=1)
            ])
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {len(itineraries)} Hanoi itineraries for {city.name}. '
                f'Created {created_count}, updated {len(itineraries) - created_count}.'
            )
        )

    def default_start_time(self, session):
        return {
            "morning": time(8, 0),
            "afternoon": time(14, 0),
            "evening": time(19, 0),
        }.get(session, time(8, 0))

    def default_cost(self, session):
        return Decimal({
            "morning": "250000",
            "afternoon": "220000",
            "evening": "300000",
        }.get(session, "200000"))

    def default_cost_note(self, session):
        return {
            "morning": "Ve tham quan/di chuyen nhe",
            "afternoon": "Ve tham quan va ca phe",
            "evening": "An toi va trai nghiem dem",
        }.get(session, "Chi phi du kien")

    def get_hanoi_city(self):
        city = (
            City.objects.filter(name__iexact='Hà Nội').first()
            or City.objects.filter(name__iexact='Ha Noi').first()
            or City.objects.filter(name__icontains='Noi').first()
            or City.objects.filter(name__icontains='Nội').first()
        )
        if city:
            return city

        country, _ = Country.objects.get_or_create(
            code='VN',
            defaults={'name': 'Vietnam', 'is_popular': True},
        )
        return City.objects.create(
            name='Ha Noi',
            country=country,
            is_popular=True,
            description='Thủ đô Việt Nam với phố cổ, hồ nước, di sản văn hóa và ẩm thực đặc trưng.',
        )
