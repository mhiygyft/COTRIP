from datetime import datetime, time, timedelta
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.functions import TruncDate
from django.utils import timezone

from flights.models import Aircraft, Airline, Airport, Flight, Route


class Command(BaseCommand):
    help = 'Ensure enough demo flights exist for multi-city booking searches.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=180, help='Number of future days to seed.')
        parser.add_argument('--flights-per-route', type=int, default=1, help='Flights per route per day.')

    def handle(self, *args, **options):
        days = max(1, options['days'])
        flights_per_route = max(1, options['flights_per_route'])

        airlines = list(Airline.objects.filter(is_active=True).order_by('id'))
        aircraft = list(Aircraft.objects.filter(is_active=True).order_by('id'))
        airports = list(Airport.objects.filter(is_popular=True, is_active=True).order_by('id'))

        if not airlines or not aircraft or len(airports) < 2:
            self.stdout.write(self.style.ERROR('Need active airlines, aircraft and at least 2 popular airports.'))
            return

        with transaction.atomic():
            routes = self.ensure_routes(airports)
            created = self.ensure_flights(routes, airlines, aircraft, days, flights_per_route)

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} additional multi-city demo flights.'))

    def ensure_routes(self, airports):
        routes = []
        for origin in airports:
            for destination in airports:
                if origin == destination:
                    continue
                distance = self.estimate_distance_km(origin, destination)
                duration = max(45, int(distance / 650 * 60) + 30)
                base_price = Decimal(max(900000, int(distance * 1800))).quantize(Decimal('1'))
                route, _ = Route.objects.get_or_create(
                    origin=origin,
                    destination=destination,
                    defaults={
                        'distance_km': distance,
                        'typical_duration_minutes': duration,
                        'is_popular': True,
                        'is_domestic': origin.country_id == destination.country_id,
                        'base_price': base_price,
                    },
                )
                routes.append(route)
        return routes

    def ensure_flights(self, routes, airlines, aircraft, days, flights_per_route):
        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=days)
        existing_keys = set(
            Flight.objects
            .filter(departure_time__date__range=(start_date, end_date))
            .annotate(flight_date=TruncDate('departure_time'))
            .values_list('origin_id', 'destination_id', 'flight_date')
        )
        new_flights = []

        for offset in range(days + 1):
            flight_date = start_date + timedelta(days=offset)
            for route_index, route in enumerate(routes):
                if (route.origin_id, route.destination_id, flight_date) in existing_keys:
                    continue
                needed = flights_per_route
                for sequence in range(needed):
                    airline = airlines[(route_index + offset + sequence) % len(airlines)]
                    aircraft_type = aircraft[(route_index + sequence) % len(aircraft)]
                    departure_time = self.departure_datetime(flight_date, route_index, sequence)
                    arrival_time = departure_time + timedelta(minutes=route.typical_duration_minutes)
                    economy_price = route.base_price * (Decimal('1.35') if airline.is_low_cost else Decimal('1.65'))

                    new_flights.append(Flight(
                        flight_number=self.flight_number(route.id, offset, sequence),
                        airline=airline,
                        aircraft=aircraft_type,
                        origin=route.origin,
                        destination=route.destination,
                        route=route,
                        departure_time=departure_time,
                        arrival_time=arrival_time,
                        departure_terminal='T1',
                        arrival_terminal='T1',
                        duration_minutes=route.typical_duration_minutes,
                        distance_km=route.distance_km,
                        stops=0,
                        economy_price=economy_price.quantize(Decimal('0.01')),
                        premium_economy_price=(economy_price * Decimal('1.5')).quantize(Decimal('0.01')) if aircraft_type.premium_economy_seats else None,
                        business_price=(economy_price * Decimal('3.0')).quantize(Decimal('0.01')) if aircraft_type.business_seats else None,
                        first_class_price=(economy_price * Decimal('5.0')).quantize(Decimal('0.01')) if aircraft_type.first_class_seats else None,
                        economy_available=max(12, int(aircraft_type.economy_seats * 0.55)),
                        premium_economy_available=max(0, int(aircraft_type.premium_economy_seats * 0.5)),
                        business_available=max(0, int(aircraft_type.business_seats * 0.45)),
                        first_class_available=max(0, int(aircraft_type.first_class_seats * 0.35)),
                    ))

        Flight.objects.bulk_create(new_flights, batch_size=1000, ignore_conflicts=True)
        return len(new_flights)

    def departure_datetime(self, flight_date, route_index, sequence):
        hour = 6 + ((route_index * 3 + sequence * 5) % 15)
        minute = (route_index * 7 + sequence * 20) % 60
        naive = datetime.combine(flight_date, time(hour=hour, minute=minute))
        return timezone.make_aware(naive, timezone.get_current_timezone())

    def flight_number(self, route_id, offset, sequence):
        return f'{(route_id % 90) + 10}{offset % 100:02d}{sequence + 1}'

    def estimate_distance_km(self, origin, destination):
        if all([origin.latitude, origin.longitude, destination.latitude, destination.longitude]):
            lat1, lon1 = radians(float(origin.latitude)), radians(float(origin.longitude))
            lat2, lon2 = radians(float(destination.latitude)), radians(float(destination.longitude))
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            return max(80, int(6371 * 2 * asin(sqrt(value))))
        return 550
