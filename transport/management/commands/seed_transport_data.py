from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from transport.models import TransportProvider, TransportRoute, TransportStation, TransportTrip


class Command(BaseCommand):
    help = 'Seed train and bus demo data for Vietnam routes.'

    def handle(self, *args, **options):
        with transaction.atomic():
            stations = self.create_stations()
            providers = self.create_providers()
            routes = self.create_routes(stations)
            created = self.create_trips(routes, providers)
        self.stdout.write(self.style.SUCCESS(f'Seeded transport data: {created} trips.'))

    def create_stations(self):
        data = [
            ('train_station', 'Ga Ha Noi', 'Ha Noi', '120 Le Duan, Hoan Kiem'),
            ('train_station', 'Ga Hue', 'Hue', '2 Bui Thi Xuan'),
            ('train_station', 'Ga Da Nang', 'Da Nang', '791 Hai Phong'),
            ('train_station', 'Ga Nha Trang', 'Nha Trang', '17 Thai Nguyen'),
            ('train_station', 'Ga Sai Gon', 'TP. Ho Chi Minh', '1 Nguyen Thong'),
            ('train_station', 'Ga Lao Cai', 'Lao Cai', 'Khanh Yen'),
            ('bus_station', 'Ben xe My Dinh', 'Ha Noi', '20 Pham Hung'),
            ('bus_station', 'Sa Pa Bus Station', 'Sa Pa', 'Ngu Chi Son'),
            ('bus_station', 'Ben xe Bai Chay', 'Ha Long', 'Bai Chay'),
            ('bus_station', 'Da Nang City Pickup', 'Da Nang', 'Trung tam Da Nang'),
            ('bus_station', 'Hoi An Pickup', 'Hoi An', 'Nguyen Tat Thanh'),
            ('bus_station', 'Ben xe Mien Dong', 'TP. Ho Chi Minh', '292 Dinh Bo Linh'),
            ('bus_station', 'Da Lat Bus Station', 'Da Lat', 'To Hien Thanh'),
            ('bus_station', 'Vung Tau Bus Station', 'Vung Tau', 'Nam Ky Khoi Nghia'),
        ]
        stations = {}
        for station_type, name, city, address in data:
            station, _ = TransportStation.objects.get_or_create(
                name=name,
                city=city,
                defaults={'station_type': station_type, 'address': address, 'is_popular': True},
            )
            stations[(city, station_type)] = station
            stations[name] = station
        return stations

    def create_providers(self):
        data = [
            ('train', 'Duong sat Viet Nam', 'VNR'),
            ('train', 'SE Express', 'SE'),
            ('bus', 'Sapa Express', 'SPE'),
            ('bus', 'Phuong Trang', 'FUTA'),
            ('bus', 'Hanh Cafe', 'HANH'),
            ('bus', 'Limousine Vietnam', 'LIMO'),
        ]
        providers = {}
        for provider_type, name, code in data:
            provider, _ = TransportProvider.objects.get_or_create(
                name=name,
                defaults={'provider_type': provider_type, 'code': code, 'rating': Decimal('4.6')},
            )
            providers[code] = provider
        return providers

    def create_routes(self, stations):
        route_specs = [
            ('train', 'Ga Ha Noi', 'Ga Hue', 688, 820),
            ('train', 'Ga Ha Noi', 'Ga Da Nang', 791, 980),
            ('train', 'Ga Da Nang', 'Ga Nha Trang', 524, 610),
            ('train', 'Ga Nha Trang', 'Ga Sai Gon', 411, 480),
            ('train', 'Ga Ha Noi', 'Ga Lao Cai', 296, 480),
            ('bus', 'Ben xe My Dinh', 'Sa Pa Bus Station', 315, 360),
            ('bus', 'Ben xe My Dinh', 'Ben xe Bai Chay', 155, 180),
            ('bus', 'Da Nang City Pickup', 'Hoi An Pickup', 30, 55),
            ('bus', 'Ben xe Mien Dong', 'Da Lat Bus Station', 300, 420),
            ('bus', 'Ben xe Mien Dong', 'Vung Tau Bus Station', 105, 150),
        ]
        routes = []
        for transport_type, origin_name, destination_name, distance, duration in route_specs:
            origin = stations[origin_name]
            destination = stations[destination_name]
            route, _ = TransportRoute.objects.get_or_create(
                transport_type=transport_type,
                origin=origin,
                destination=destination,
                defaults={'distance_km': distance, 'typical_duration_minutes': duration},
            )
            reverse_route, _ = TransportRoute.objects.get_or_create(
                transport_type=transport_type,
                origin=destination,
                destination=origin,
                defaults={'distance_km': distance, 'typical_duration_minutes': duration},
            )
            routes.extend([route, reverse_route])
        return routes

    def create_trips(self, routes, providers):
        created = 0
        start_date = timezone.localdate()
        for day_offset in range(90):
            travel_date = start_date + timedelta(days=day_offset)
            for index, route in enumerate(routes):
                if route.transport_type == 'train':
                    provider = providers['VNR'] if index % 2 == 0 else providers['SE']
                    classes = [('soft_seat', 350000), ('soft_sleeper', 620000)]
                    depart_hours = [7, 19]
                    prefix = 'SE'
                else:
                    provider = providers[['SPE', 'FUTA', 'HANH', 'LIMO'][index % 4]]
                    classes = [('standard', 180000), ('sleeper', 260000), ('vip', 420000)]
                    depart_hours = [6, 14, 22]
                    prefix = 'BUS'

                for seq, (seat_class, price) in enumerate(classes[:len(depart_hours)]):
                    departure = timezone.make_aware(datetime.combine(travel_date, time(depart_hours[seq], (index * 7) % 60)))
                    arrival = departure + timedelta(minutes=route.typical_duration_minutes)
                    trip_code = f'{prefix}{route.id:03d}{day_offset:02d}{seq + 1}'
                    _, was_created = TransportTrip.objects.get_or_create(
                        provider=provider,
                        trip_code=trip_code,
                        departure_time=departure,
                        defaults={
                            'route': route,
                            'arrival_time': arrival,
                            'seat_class': seat_class,
                            'vehicle_type': 'Tau SE' if route.transport_type == 'train' else 'Limousine/Giuong nam',
                            'pickup_note': route.origin.address,
                            'dropoff_note': route.destination.address,
                            'base_price': Decimal(price + route.distance_km * 600),
                            'available_seats': 32 if route.transport_type == 'train' else 18,
                            'total_seats': 64 if route.transport_type == 'train' else 24,
                        },
                    )
                    if was_created:
                        created += 1
        return created
