from datetime import time
from decimal import Decimal

from django.core.management.base import BaseCommand

from hotels.models import City, Hotel, Itinerary, ItineraryStop


class Command(BaseCommand):
    help = "Seed baseline editable planner itineraries for every active hotel city."

    def handle(self, *args, **options):
        city_ids = (
            Hotel.objects.filter(is_active=True)
            .values_list("city_id", flat=True)
            .distinct()
        )
        cities = City.objects.filter(id__in=city_ids).select_related("country")
        created = 0
        updated = 0

        for city in cities:
            if Itinerary.objects.filter(city=city, created_by__isnull=True, is_active=True).exists():
                continue

            itinerary, was_created = Itinerary.objects.update_or_create(
                city=city,
                title=f"{city.name} 3 ngày tự túc",
                created_by=None,
                defaults={
                    "days": 3,
                    "description": (
                        f"Lịch trình cơ bản cho {city.name}: có di chuyển, điểm tham quan, "
                        "ăn uống, cafe/chill và thời gian nghỉ phù hợp để người dùng chỉnh sửa."
                    ),
                    "is_active": True,
                    "order": 20,
                },
            )
            itinerary.stops.all().delete()
            ItineraryStop.objects.bulk_create(self.build_stops(itinerary, city.name))
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded baseline planner itineraries. Created {created}, updated {updated}."
        ))

    def build_stops(self, itinerary, city_name):
        image_url = itinerary.city.image_source_url
        rows = [
            (1, "morning", "transport", time(8, 0), f"Di chuyển đến {city_name}", f"Đến {city_name}, nhận xe/taxi và di chuyển về khu lưu trú.", 180000, "Taxi/Grab hoặc xe đưa đón"),
            (1, "morning", "attraction", time(10, 0), f"Check-in trung tâm {city_name}", f"Đi bộ làm quen khu trung tâm, chọn vài góc chụp ảnh và điểm nổi bật gần khách sạn.", 80000, "Vé/chi phí nhẹ"),
            (1, "afternoon", "food", time(12, 0), f"Ăn trưa đặc sản {city_name}", f"Thử món địa phương nổi bật, ưu tiên quán dễ đi và phù hợp nhóm bạn.", 120000, "Bữa trưa/người"),
            (1, "afternoon", "accommodation", time(15, 0), f"Nhận phòng tại {city_name}", f"Nhận phòng khách sạn, homestay hoặc local stay đã chọn.", 650000, "Chi phí lưu trú/người"),
            (1, "evening", "food", time(19, 0), f"Ăn tối và dạo đêm {city_name}", f"Ăn tối, đi chợ đêm/phố đi bộ hoặc khu cafe buổi tối.", 220000, "Ăn tối và ăn vặt"),

            (2, "morning", "transport", time(8, 0), f"Di chuyển tới điểm tham quan chính", f"Đặt xe hoặc thuê xe máy để đi cụm điểm tham quan trong ngày.", 180000, "Di chuyển trong ngày"),
            (2, "morning", "attraction", time(9, 0), f"Điểm tham quan nổi bật {city_name}", f"Tham quan điểm nổi bật nhất của {city_name}, dành thời gian chụp ảnh và trải nghiệm.", 180000, "Vé tham quan"),
            (2, "afternoon", "food", time(12, 0), f"Ăn trưa địa phương", "Ăn trưa gần điểm tham quan để tiết kiệm thời gian di chuyển.", 130000, "Bữa trưa/người"),
            (2, "afternoon", "attraction", time(14, 30), f"Cafe/chill hoặc viewpoint {city_name}", f"Chọn quán cafe đẹp, viewpoint, bãi biển, hồ hoặc khu phố nhỏ để nghỉ giữa lịch trình.", 120000, "Cafe/vé nhẹ"),
            (2, "evening", "food", time(19, 0), f"Ăn tối/chợ đêm {city_name}", f"Ăn tối, thử món ăn vặt và mua quà địa phương.", 240000, "Ăn tối/người"),

            (3, "morning", "attraction", time(8, 30), f"Trải nghiệm địa phương {city_name}", f"Ghé làng nghề, chợ địa phương, khu check-in nhỏ hoặc hoạt động nhẹ trước khi rời đi.", 160000, "Trải nghiệm địa phương"),
            (3, "afternoon", "food", time(12, 0), f"Bữa trưa cuối chuyến", "Ăn trưa, mua quà và kiểm tra lại hành lý.", 130000, "Bữa trưa/người"),
            (3, "afternoon", "transport", time(15, 0), f"Di chuyển ra sân bay/ga/bến xe", f"Đặt xe từ khách sạn ra sân bay, ga hoặc bến xe để kết thúc hành trình.", 220000, "Xe đưa tiễn"),
        ]
        return [
            ItineraryStop(
                itinerary=itinerary,
                day_number=day,
                session=session,
                activity_type=activity_type,
                start_time=start_time,
                place_name=title,
                description=description,
                duration_hours=Decimal("1.5"),
                estimated_cost=Decimal(cost),
                currency="VND",
                cost_note=cost_note,
                image_url=image_url,
                google_maps_url=f"https://www.google.com/maps/search/?api=1&query={title.replace(' ', '+')}",
                order=index,
            )
            for index, (day, session, activity_type, start_time, title, description, cost, cost_note)
            in enumerate(rows, start=1)
        ]
