from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand

from hotels.models import City, Itinerary, ItineraryStop


class Command(BaseCommand):
    help = "Seed sample Da Nang itineraries."

    def handle(self, *args, **options):
        city = City.objects.filter(name__iexact="Da Nang").first()
        if not city:
            self.stdout.write(self.style.ERROR("Da Nang city was not found."))
            return

        image_url = city.image_source_url
        itineraries = [
            {
                "title": "Đà Nẵng 3 ngày 2 đêm",
                "days": 3,
                "description": "Lịch trình biển, bán đảo Sơn Trà, Ngũ Hành Sơn và phố đêm ven sông Hàn.",
                "order": 1,
                "stops": [
                    (1, "morning", "Bãi biển Mỹ Khê", "Tắm biển, đi dạo bờ cát và bắt đầu ngày mới bằng cà phê ven biển.", 2.0, "https://www.google.com/maps/search/?api=1&query=My+Khe+Beach+Da+Nang"),
                    (1, "afternoon", "Bảo tàng Điêu khắc Chăm", "Tìm hiểu văn hóa Chăm Pa qua bộ sưu tập hiện vật đặc sắc.", 1.5, "https://www.google.com/maps/search/?api=1&query=Da+Nang+Museum+of+Cham+Sculpture"),
                    (1, "evening", "Cầu Rồng và sông Hàn", "Ăn tối gần sông Hàn, dạo cầu Rồng và xem không khí thành phố về đêm.", 2.0, "https://www.google.com/maps/search/?api=1&query=Dragon+Bridge+Da+Nang"),
                    (2, "morning", "Bán đảo Sơn Trà", "Đi chùa Linh Ứng, ngắm tượng Phật Quan Âm và toàn cảnh vịnh Đà Nẵng.", 3.0, "https://www.google.com/maps/search/?api=1&query=Son+Tra+Peninsula+Da+Nang"),
                    (2, "afternoon", "Ngũ Hành Sơn", "Khám phá hang động, chùa cổ và các điểm nhìn từ núi đá vôi.", 2.5, "https://www.google.com/maps/search/?api=1&query=Marble+Mountains+Da+Nang"),
                    (2, "evening", "Chợ đêm Sơn Trà", "Thưởng thức hải sản, đồ ăn đường phố và mua quà lưu niệm.", 2.0, "https://www.google.com/maps/search/?api=1&query=Son+Tra+Night+Market+Da+Nang"),
                    (3, "morning", "Bà Nà Hills", "Đi cáp treo, tham quan Cầu Vàng và khu làng Pháp.", 4.0, "https://www.google.com/maps/search/?api=1&query=Ba+Na+Hills+Da+Nang"),
                    (3, "afternoon", "Suối khoáng nóng Núi Thần Tài", "Thư giãn sau hành trình với tắm khoáng và khu công viên nước.", 3.0, "https://www.google.com/maps/search/?api=1&query=Nui+Than+Tai+Hot+Springs"),
                    (3, "evening", "Ẩm thực hải sản ven biển", "Kết thúc chuyến đi bằng bữa tối hải sản ở khu Võ Nguyên Giáp.", 2.0, "https://www.google.com/maps/search/?api=1&query=Da+Nang+seafood+Vo+Nguyen+Giap"),
                ],
            },
            {
                "title": "Đà Nẵng 4 ngày 3 đêm",
                "days": 4,
                "description": "Lịch trình chậm hơn, kết hợp Đà Nẵng với Hội An trong một ngày gần kề.",
                "order": 2,
                "stops": [
                    (1, "morning", "Bãi biển Mỹ Khê", "Nghỉ biển nhẹ nhàng, tắm nắng và dùng bữa sáng ven biển.", 2.0, "https://www.google.com/maps/search/?api=1&query=My+Khe+Beach+Da+Nang"),
                    (1, "afternoon", "Cầu Tình Yêu", "Đi dạo ven sông Hàn, chụp ảnh với cầu Tình Yêu và tượng cá chép hóa rồng.", 1.5, "https://www.google.com/maps/search/?api=1&query=Love+Bridge+Da+Nang"),
                    (1, "evening", "Cầu Rồng", "Thưởng thức bữa tối trung tâm và xem cầu Rồng nếu đi đúng cuối tuần.", 2.0, "https://www.google.com/maps/search/?api=1&query=Dragon+Bridge+Da+Nang"),
                    (2, "morning", "Bán đảo Sơn Trà", "Thăm chùa Linh Ứng, ngắm biển và các cung đường xanh quanh bán đảo.", 3.0, "https://www.google.com/maps/search/?api=1&query=Son+Tra+Peninsula+Da+Nang"),
                    (2, "afternoon", "Ngũ Hành Sơn", "Dành thời gian leo núi, ghé làng đá mỹ nghệ Non Nước.", 2.5, "https://www.google.com/maps/search/?api=1&query=Marble+Mountains+Da+Nang"),
                    (2, "evening", "Chợ Cồn", "Ăn tối với mì Quảng, bánh tráng cuốn thịt heo và các món địa phương.", 1.5, "https://www.google.com/maps/search/?api=1&query=Con+Market+Da+Nang"),
                    (3, "morning", "Bà Nà Hills", "Khởi hành sớm để đi Cầu Vàng, cáp treo và các khu vui chơi.", 4.0, "https://www.google.com/maps/search/?api=1&query=Ba+Na+Hills+Da+Nang"),
                    (3, "afternoon", "Công viên Châu Á", "Quay lại trung tâm, thư giãn và chơi nhẹ ở Asia Park nếu còn thời gian.", 2.0, "https://www.google.com/maps/search/?api=1&query=Asia+Park+Da+Nang"),
                    (3, "evening", "Helio Night Market", "Ăn tối, nghe nhạc và thử các món ăn vặt tại chợ đêm Helio.", 2.0, "https://www.google.com/maps/search/?api=1&query=Helio+Night+Market+Da+Nang"),
                    (4, "morning", "Phố cổ Hội An", "Đi Hội An buổi sáng, thăm nhà cổ, chùa Cầu và các con hẻm đèn lồng.", 3.0, "https://www.google.com/maps/search/?api=1&query=Hoi+An+Ancient+Town"),
                    (4, "afternoon", "Rừng dừa Bảy Mẫu", "Trải nghiệm thuyền thúng và không gian sông nước gần Hội An.", 2.0, "https://www.google.com/maps/search/?api=1&query=Bay+Mau+Coconut+Forest"),
                    (4, "evening", "Hội An về đêm", "Ăn cao lầu, thả hoa đăng và quay lại Đà Nẵng sau bữa tối.", 2.0, "https://www.google.com/maps/search/?api=1&query=Hoi+An+Night+Market"),
                ],
            },
        ]

        created_count = 0
        for data in itineraries:
            itinerary, created = Itinerary.objects.update_or_create(
                city=city,
                title=data["title"],
                defaults={
                    "days": data["days"],
                    "description": data["description"],
                    "is_active": True,
                    "order": data["order"],
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
                in enumerate(data["stops"], start=1)
            ])
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(itineraries)} Da Nang itineraries. "
                f"Created {created_count}, updated {len(itineraries) - created_count}."
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
            "morning": "350000",
            "afternoon": "250000",
            "evening": "300000",
        }.get(session, "200000"))

    def default_cost_note(self, session):
        return {
            "morning": "Vé tham quan/di chuyển nhẹ",
            "afternoon": "Vé tham quan và ăn nhẹ",
            "evening": "Ăn tối và trải nghiệm đêm",
        }.get(session, "Chi phí dự kiến")
