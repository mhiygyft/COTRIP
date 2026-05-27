import json
import logging
from decimal import Decimal

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
from hotels.models import Hotel
from packages.models import TravelPackage

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


def _hotel_recommendations(request, message):
    hotels = (
        Hotel.objects.filter(is_active=True)
        .select_related("city", "city__country")
        .prefetch_related("images")
    )
    items = []
    for hotel in hotels[:80]:
        score = _score(
            message,
            hotel.name,
            hotel.city.name,
            hotel.city.country.name,
            hotel.address,
            hotel.description,
            hotel.star_rating,
        )
        if score or len(items) < 4:
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
    for package in packages[:80]:
        score = _score(
            message,
            package.title,
            package.destination_city,
            package.destination_country,
            package.package_type,
            package.description,
            package.short_description,
        )
        if score or len(items) < 4:
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
    for activity in activities[:80]:
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
        if score or len(items) < 4:
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
    flight_words = {"bay", "vé", "ve", "máy", "may", "flight", "airport", "sân", "san", "chuyến", "chuyen"}
    query_tokens = set(_normalize(message).split())
    query_has_flight_intent = bool(query_tokens & flight_words)
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
    for flight in flights[:40]:
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


def _collect_recommendations(request, message):
    items = []
    items.extend(_hotel_recommendations(request, message))
    items.extend(_package_recommendations(request, message))
    items.extend(_activity_recommendations(request, message))
    items.extend(_flight_recommendations(request, message))
    ranked = sorted(items, key=lambda item: item["score"], reverse=True)
    return [{key: value for key, value in item.items() if key != "score"} for item in ranked[:6]]


def _fallback_answer(message, recommendations):
    if not recommendations:
        return (
            "Hiện tại mình chưa tìm thấy lựa chọn thật sự khớp với yêu cầu này. "
            "Bạn có thể nói rõ điểm đến, ngân sách, số ngày đi hoặc kiểu chuyến đi mong muốn."
        )

    names = ", ".join(item["title"] for item in recommendations[:3])
    return (
        f"Dựa trên yêu cầu của bạn, mình gợi ý các lựa chọn đang có sẵn trên website: {names}. "
        "Bạn có thể bấm vào từng thẻ để xem chi tiết và đặt phòng, đặt tour hoặc đặt vé."
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
        "Trả lời bằng tiếng Việt có dấu, thân thiện và ngắn gọn. "
        "Chỉ đề xuất các khách sạn, tour, trải nghiệm hoặc chuyến bay có trong INVENTORY. "
        "Nếu dữ liệu chưa đủ, hãy hỏi thêm 1 câu hỏi ngắn về điểm đến, ngân sách hoặc thời gian."
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
        "max_output_tokens": 450,
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

    return JsonResponse(
        {
            "answer": answer,
            "recommendations": recommendations,
            "used_ai": bool(ai_answer),
        }
    )
