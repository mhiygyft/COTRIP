import json
import logging
import re
from decimal import Decimal
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from text_unidecode import unidecode

from activities.models import Activity
from flights.models import Flight
from hotels.models import City, Hotel
from packages.models import TravelPackage
from transport.models import TransportTrip

logger = logging.getLogger(__name__)


def _normalize(value):
    return unidecode(str(value or "")).lower()


def _money(value, currency="VND"):
    if value is None:
        return ""
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    return f"{amount:,.0f} {currency}".replace(",", ".")


def _absolute_url(request, url):
    return request.build_absolute_uri(url)


def _score(query, *fields):
    normalized_query = _normalize(query)
    haystack = _normalize(" ".join(str(field or "") for field in fields))
    tokens = [token for token in normalized_query.split() if len(token) > 1]
    if not tokens:
        return 0
    return sum(3 if token in haystack else 0 for token in tokens)


def _message_tokens(message):
    return set(_normalize(message).split())


def _extract_days(message, default=3):
    match = re.search(r"(\d+)\s*(ngay|ngày|day|days)", _normalize(message))
    if not match:
        return default
    return max(1, min(int(match.group(1)), 7))


def _extract_travelers(message, default=2):
    normalized = _normalize(message)
    match = re.search(r"(\d+)\s*(nguoi|người|khach|khách|pax)", normalized)
    if not match:
        return default
    return max(1, min(int(match.group(1)), 20))


def _extract_budget(message):
    normalized = _normalize(message).replace(".", "").replace(",", "")
    million_match = re.search(r"(\d+)\s*(trieu|triệu|m)", normalized)
    if million_match:
        return int(million_match.group(1)) * 1000000
    number_match = re.search(r"(\d{6,})", normalized)
    if number_match:
        return int(number_match.group(1))
    return 0


def _extract_destination(message, recommendations=None):
    normalized = _normalize(message)
    for city in City.objects.filter(is_popular=True).order_by("-is_popular", "name"):
        if _normalize(city.name) in normalized:
            return city.name
    for city in City.objects.order_by("name"):
        if _normalize(city.name) in normalized:
            return city.name
    for item in recommendations or []:
        subtitle = item.get("subtitle", "")
        if subtitle:
            return subtitle.split(",", 1)[0].split(" - ", 1)[0].strip()
    return ""


def _has_plan_intent(message):
    normalized = _normalize(message)
    if any(phrase in normalized for phrase in [
        "lich trinh", "lịch trình", "ke hoach", "kế hoạch", "len plan",
        "lên plan", "itinerary", "timeline", "plan chi tiet", "plan chi tiết",
    ]):
        return True
    asks_for_suggestion = any(phrase in normalized for phrase in ["goi y", "gợi ý"])
    has_trip_length = bool(re.search(r"\d+\s*(ngay|ngày|day|days)", normalized))
    return asks_for_suggestion and has_trip_length and bool(_extract_destination(message))


def _has_compare_intent(message):
    normalized = _normalize(message)
    return any(phrase in normalized for phrase in [
        "lua chon", "lựa chọn", "can nhac", "cân nhắc", "so sanh",
        "so sánh", "nen chon", "nên chọn", "goi y", "gợi ý",
    ])


def _has_service_intent(message):
    normalized = _normalize(message)
    return any(phrase in normalized for phrase in [
        "sim", "data", "doi tien", "đổi tiền", "bao hiem", "bảo hiểm",
        "khach nuoc ngoai", "khách nước ngoài", "foreign", "airport",
    ])


def _hotel_recommendations(request, message):
    hotels = (
        Hotel.objects.filter(is_active=True)
        .select_related("city", "city__country")
        .prefetch_related("images")
    )
    items = []
    for hotel in hotels[:120]:
        score = _score(
            message,
            hotel.name,
            hotel.city.name,
            hotel.city.country.name,
            hotel.address,
            hotel.description,
            hotel.star_rating,
        )
        if score or (len(items) < 5 and not _has_service_intent(message)):
            items.append(
                {
                    "type": "Khách sạn",
                    "title": hotel.name,
                    "subtitle": f"{hotel.city.name}, {hotel.city.country.name} - {hotel.star_rating} sao",
                    "description": hotel.description[:220],
                    "price": f"Từ {_money(hotel.price_from, hotel.currency)}/đêm",
                    "image": hotel.primary_image_url,
                    "url": _absolute_url(request, hotel.get_absolute_url()),
                    "score": score + (2 if hotel.is_featured else 0),
                }
            )
    return items


def _package_recommendations(request, message):
    packages = TravelPackage.objects.filter(is_active=True).prefetch_related("images")
    items = []
    for package in packages[:100]:
        score = _score(
            message,
            package.title,
            package.destination_city,
            package.destination_country,
            package.package_type,
            package.description,
            package.short_description,
        )
        if score or (len(items) < 5 and not _has_service_intent(message)):
            items.append(
                {
                    "type": "Tour",
                    "title": package.title,
                    "subtitle": f"{package.destination_city}, {package.destination_country} - {package.duration_days} ngày {package.duration_nights} đêm",
                    "description": package.short_description or package.description[:220],
                    "price": f"Từ {_money(package.base_price_per_person)}/khách",
                    "image": package.primary_image_url,
                    "url": _absolute_url(request, reverse("packages:detail", kwargs={"package_id": package.id})),
                    "score": score + (2 if package.featured else 0),
                }
            )
    return items


def _activity_recommendations(request, message):
    activities = (
        Activity.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
    )
    items = []
    for activity in activities[:120]:
        score = _score(
            message,
            activity.title,
            activity.city,
            activity.country,
            activity.category.name,
            activity.difficulty,
            activity.description,
            activity.short_description,
        )
        if score or (len(items) < 5 and not _has_service_intent(message)):
            items.append(
                {
                    "type": "Trải nghiệm",
                    "title": activity.title,
                    "subtitle": f"{activity.city}, {activity.country} - {activity.duration_hours} giờ",
                    "description": activity.short_description or activity.description[:220],
                    "price": f"Từ {_money(activity.price_adult)}/người lớn",
                    "image": activity.primary_image_url,
                    "url": _absolute_url(request, reverse("activities:detail", kwargs={"activity_id": activity.id})),
                    "score": score + (2 if activity.featured else 0),
                }
            )
    return items


def _flight_recommendations(request, message):
    flight_words = {"bay", "ve", "vé", "may", "máy", "flight", "airport", "san", "sân", "chuyen", "chuyến"}
    query_has_flight_intent = bool(_message_tokens(message) & flight_words)
    flights = (
        Flight.objects.filter(
            is_active=True,
            status="scheduled",
            departure_time__gte=timezone.now(),
        )
        .filter(
            Q(economy_available__gt=0)
            | Q(premium_economy_available__gt=0)
            | Q(business_available__gt=0)
            | Q(first_class_available__gt=0)
        )
        .select_related("airline", "origin", "destination")
    )
    items = []
    for flight in flights[:80]:
        score = _score(
            message,
            flight.flight_code,
            flight.airline.name,
            flight.origin.city,
            flight.destination.city,
            flight.origin.iata_code,
            flight.destination.iata_code,
        )
        if query_has_flight_intent:
            score += 2
        if score or query_has_flight_intent:
            items.append(
                {
                    "type": "Chuyến bay",
                    "title": f"{flight.flight_code}: {flight.origin.city} -> {flight.destination.city}",
                    "subtitle": f"{flight.airline.name} - {flight.departure_time:%d/%m/%Y %H:%M}",
                    "description": f"Bay {flight.duration_display}, {'bay thẳng' if flight.is_direct else str(flight.stops) + ' điểm dừng'}.",
                    "price": f"Từ {_money(flight.economy_price)}/khách",
                    "image": "",
                    "url": _absolute_url(request, reverse("flights:detail", kwargs={"flight_id": flight.id})),
                    "score": score,
                }
            )
    return items


def _transport_recommendations(request, message):
    transport_words = {"tau", "tàu", "xe", "bus", "limousine", "transport", "ga", "ben", "bến"}
    query_has_transport_intent = bool(_message_tokens(message) & transport_words)
    trips = (
        TransportTrip.objects.filter(
            is_active=True,
            status="scheduled",
            available_seats__gt=0,
            departure_time__gte=timezone.now(),
        )
        .select_related("provider", "route", "route__origin", "route__destination")
    )
    items = []
    for trip in trips[:80]:
        score = _score(
            message,
            trip.trip_code,
            trip.provider.name,
            trip.route.origin.city,
            trip.route.destination.city,
            trip.seat_class,
            trip.vehicle_type,
        )
        if query_has_transport_intent:
            score += 2
        if score or query_has_transport_intent:
            items.append(
                {
                    "type": "Tàu/xe khách",
                    "title": f"{trip.route.origin.city} -> {trip.route.destination.city}",
                    "subtitle": f"{trip.provider.name} - {trip.departure_time:%d/%m/%Y %H:%M}",
                    "description": f"{trip.get_seat_class_display()} · {trip.duration_display}. {trip.pickup_note or ''}",
                    "price": f"Từ {_money(trip.base_price)}/khách",
                    "image": "",
                    "url": _absolute_url(request, reverse("transport:search")),
                    "score": score,
                }
            )
    return items


def _arrival_service_recommendations(request, message):
    normalized = _normalize(message)
    service_intent = _has_service_intent(message) or any(phrase in normalized for phrase in [
        "san bay", "sân bay", "don san bay", "đón sân bay",
    ])
    if not service_intent and not _has_compare_intent(message) and not _has_plan_intent(message):
        return []
    services = [
        ("Dịch vụ đến nơi", "Explorer 15GB SIM", "SIM 15GB - nhận tại sân bay hoặc khách sạn", "Phù hợp khách đi nhiều thành phố, cần data ổn định để dùng bản đồ, chat và mạng xã hội.", "280.000 VND", reverse("sim_cards"), 30 if "sim" in normalized or "data" in normalized else 12),
        ("Dịch vụ đến nơi", "Đổi tiền khi nhận SIM", "USD/EUR/KRW/JPY sang VND", "Hỗ trợ đổi tiền tại điểm nhận SIM hoặc điểm hẹn, phù hợp khách quốc tế mới đến Việt Nam.", "Phí giữ dịch vụ 50.000 VND", reverse("sim_cards"), 30 if "doi tien" in normalized else 12),
        ("Dịch vụ đến nơi", "Bảo hiểm du lịch ngắn ngày", "Gói cơ bản cho khách quốc tế", "Có thể thêm khi gửi yêu cầu SIM/dịch vụ đến nơi.", "Từ 120.000 VND", reverse("sim_cards"), 30 if "bao hiem" in normalized else 12),
        ("Đặt xe", "Đặt xe trung chuyển", "Sân bay, khách sạn hoặc điểm đã đặt", "Dùng khi cần đi từ sân bay về khách sạn, từ khách sạn ra sân bay hoặc giữa các điểm trong lịch trình.", "Tính theo tuyến", reverse("transfers"), 8 if "san bay" in normalized or "airport" in normalized else 3),
    ]
    return [
        {
            "type": item_type,
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "price": price,
            "image": "",
            "url": _absolute_url(request, url),
            "score": score,
        }
        for item_type, title, subtitle, description, price, url, score in services
    ]


def _collect_recommendations(request, message):
    items = []
    items.extend(_hotel_recommendations(request, message))
    items.extend(_package_recommendations(request, message))
    items.extend(_activity_recommendations(request, message))
    items.extend(_flight_recommendations(request, message))
    items.extend(_transport_recommendations(request, message))
    items.extend(_arrival_service_recommendations(request, message))
    ranked = sorted(items, key=lambda item: item["score"], reverse=True)
    limit = 10 if _has_plan_intent(message) or _has_compare_intent(message) else 6
    type_counts = {}
    diversified = []
    max_per_type = 3 if limit > 6 else 2
    for item in ranked:
        item_type = item["type"]
        if type_counts.get(item_type, 0) >= max_per_type:
            continue
        diversified.append(item)
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
        if len(diversified) >= limit:
            break
    return [{key: value for key, value in item.items() if key != "score"} for item in diversified]


def _items_by_type(recommendations, item_type, limit=3):
    return [item for item in recommendations if item["type"] == item_type][:limit]


def _first_by_type(recommendations, item_type):
    rows = _items_by_type(recommendations, item_type, limit=1)
    return rows[0] if rows else None


def _build_plan_answer(message, recommendations):
    days = _extract_days(message)
    hotel = _first_by_type(recommendations, "Khách sạn")
    package = _first_by_type(recommendations, "Tour")
    flight = _first_by_type(recommendations, "Chuyến bay")
    transport = _first_by_type(recommendations, "Tàu/xe khách")
    transfer = _first_by_type(recommendations, "Đặt xe")
    activities = _items_by_type(recommendations, "Trải nghiệm", limit=6)
    services = _items_by_type(recommendations, "Dịch vụ đến nơi", limit=3)

    lines = [
        f"Mình có thể lên plan {days} ngày theo dữ liệu đang có trên COTRIPVn. Bản nháp này nên chỉnh lại theo giờ bay/giờ nhận phòng thực tế:",
        "",
    ]
    for day in range(1, days + 1):
        morning_activity = activities[(day - 1) % len(activities)] if activities else None
        afternoon_activity = activities[day % len(activities)] if len(activities) > 1 else morning_activity
        lines.extend([
            f"Ngày {day}",
            f"- Sáng: {'Di chuyển/nhận xe' if day == 1 else 'Di chuyển tới điểm tham quan'}"
            f"{' · ' + (flight['title'] if flight and day == 1 else transport['title']) if (flight and day == 1) or transport else ''}.",
            "- Trưa: Ăn món địa phương gần khu tham quan, giữ lịch nhẹ để không bị quá tải.",
            f"- Chiều: {afternoon_activity['title'] if afternoon_activity else 'Chọn một trải nghiệm hoặc điểm check-in phù hợp'}"
            f"{' · ' + afternoon_activity['price'] if afternoon_activity else ''}.",
            f"- Tối: Ăn tối/chợ đêm/cafe chill. "
            f"{'Có thể ở ' + hotel['title'] + ' (' + hotel['price'] + ').' if hotel and day == 1 else 'Dành thời gian nghỉ và cân lại ngân sách.'}",
            "",
        ])

    choices = []
    if hotel:
        choices.append(f"Ở: {hotel['title']} - {hotel['price']}")
    if package:
        choices.append(f"Tour thay thế nếu muốn gọn: {package['title']} - {package['price']}")
    if flight:
        choices.append(f"Bay: {flight['title']} - {flight['price']}")
    if transport:
        choices.append(f"Tàu/xe: {transport['title']} - {transport['price']}")
    if transfer:
        choices.append(f"Trung chuyển: {transfer['title']}")
    choices.extend(f"Dịch vụ thêm: {item['title']} - {item['price']}" for item in services)

    if choices:
        lines.append("Các lựa chọn nên cân nhắc:")
        lines.extend(f"- {choice}" for choice in choices[:8])
    lines.append("Bạn nói thêm số người, ngân sách và gu du lịch, mình sẽ chỉnh timeline chi tiết hơn.")
    return "\n".join(lines)


def _planner_action(request, message, recommendations):
    if not _has_plan_intent(message):
        return None
    destination = _extract_destination(message, recommendations)
    if not destination:
        return None
    params = {
        "destination": destination,
        "days": _extract_days(message),
        "travelers": _extract_travelers(message),
        "from_chat": "1",
    }
    budget = _extract_budget(message)
    if budget:
        params["budget"] = budget
    return {
        "label": "Mở lịch trình để chỉnh sửa",
        "url": _absolute_url(request, f"{reverse('hotels:itinerary_planner')}?{urlencode(params)}"),
        "type": "itinerary_planner",
    }


def _fallback_answer(message, recommendations):
    if not recommendations:
        return (
            "Mình chưa tìm thấy lựa chọn thật sự khớp với yêu cầu này. "
            "Bạn có thể nói rõ điểm đến, ngân sách, số ngày đi hoặc kiểu chuyến đi mong muốn."
        )

    if _has_plan_intent(message):
        return _build_plan_answer(message, recommendations)

    names = ", ".join(item["title"] for item in recommendations[:3])
    if _has_compare_intent(message):
        grouped = {}
        for item in recommendations:
            grouped.setdefault(item["type"], []).append(item)
        parts = [f"Mình tìm được các lựa chọn có thể cân nhắc. Nổi bật nhất: {names}."]
        for item_type, rows in grouped.items():
            titles = "; ".join(f"{row['title']} ({row['price']})" for row in rows[:3])
            parts.append(f"- {item_type}: {titles}")
        parts.append("Bạn bấm vào từng thẻ để xem chi tiết, hoặc nói ngân sách/số ngày để mình lọc lại.")
        return "\n".join(parts)

    return (
        f"Dựa trên yêu cầu của bạn, mình gợi ý các lựa chọn đang có sẵn trên website: {names}. "
        "Mình cũng có thể lên plan theo ngày, so sánh lựa chọn hoặc tư vấn theo ngân sách nếu bạn nói rõ thêm."
    )


def _extract_openai_text(payload):
    if payload.get("output_text"):
        return payload["output_text"]

    parts = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            text = content.get("text")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def _ask_openai(message, recommendations):
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return ""

    inventory = json.dumps(recommendations, ensure_ascii=False)
    system_prompt = (
        "Bạn là chatbot tư vấn du lịch cho website COTRIPVn. "
        "Trả lời bằng tiếng Việt có dấu, tự nhiên như nhân viên tư vấn du lịch. "
        "Bạn có thể trò chuyện, hỏi thêm thông tin, so sánh lựa chọn và lên plan chi tiết theo ngày. "
        "Khi đề xuất dịch vụ có thể đặt, chỉ dùng các khách sạn, tour, trải nghiệm, chuyến bay, tàu/xe hoặc dịch vụ trong INVENTORY. "
        "Nếu người dùng muốn lịch trình, hãy chia theo Ngày/Sáng/Trưa/Chiều/Tối, nêu chi phí ước tính và lựa chọn thay thế. "
        "Nếu dữ liệu chưa đủ, hỏi tối đa 1 câu ngắn về điểm đến, ngân sách, số người hoặc số ngày."
    )
    payload = {
        "model": getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
        "input": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Yêu cầu khách hàng: {message}\n\nINVENTORY:\n{inventory}",
            },
        ],
        "max_output_tokens": 850,
    }

    try:
        response = requests.post(
            getattr(settings, "OPENAI_RESPONSES_URL", "https://api.openai.com/v1/responses"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return _extract_openai_text(response.json())
    except requests.RequestException as exc:
        logger.warning("OpenAI chatbot request failed: %s", exc)
        return ""


@csrf_exempt
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Nội dung gửi lên không hợp lệ."}, status=400)

    message = str(data.get("message", "")).strip()
    if not message:
        return JsonResponse({"error": "Vui lòng nhập nội dung cần tư vấn."}, status=400)

    recommendations = _collect_recommendations(request, message)
    ai_answer = _ask_openai(message, recommendations)
    answer = ai_answer or _fallback_answer(message, recommendations)
    actions = []
    planner_action = _planner_action(request, message, recommendations)
    if planner_action:
        actions.append(planner_action)

    return JsonResponse(
        {
            "answer": answer,
            "recommendations": recommendations,
            "actions": actions,
            "used_ai": bool(ai_answer),
        }
    )
