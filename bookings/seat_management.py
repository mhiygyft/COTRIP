"""
Seat selection and management system for flight bookings
"""
import json
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from flights.models import Flight
from .models import Booking, Passenger


class SeatType:
    """Seat type definitions"""
    ECONOMY = 'economy'
    PREMIUM_ECONOMY = 'premium_economy'
    BUSINESS = 'business'
    FIRST = 'first'
    
    CHOICES = [
        (ECONOMY, 'Economy'),
        (PREMIUM_ECONOMY, 'Premium Economy'),
        (BUSINESS, 'Business'),
        (FIRST, 'First Class'),
    ]


class SeatStatus:
    """Seat availability status"""
    AVAILABLE = 'available'
    OCCUPIED = 'occupied'
    BLOCKED = 'blocked'
    SELECTED = 'selected'
    
    CHOICES = [
        (AVAILABLE, 'Available'),
        (OCCUPIED, 'Occupied'),
        (BLOCKED, 'Blocked'),
        (SELECTED, 'Selected'),
    ]


class SeatCharacteristic:
    """Seat characteristics"""
    WINDOW = 'window'
    AISLE = 'aisle'
    MIDDLE = 'middle'
    EXIT_ROW = 'exit_row'
    BULKHEAD = 'bulkhead'
    PREMIUM = 'premium'
    
    CHOICES = [
        (WINDOW, 'Window'),
        (AISLE, 'Aisle'),
        (MIDDLE, 'Middle'),
        (EXIT_ROW, 'Exit Row'),
        (BULKHEAD, 'Bulkhead'),
        (PREMIUM, 'Premium'),
    ]


class SeatMap:
    """Flight seat map management"""
    
    def __init__(self, flight):
        self.flight = flight
        self.seat_map = self._generate_seat_map()
    
    def _generate_seat_map(self):
        """Generate a seat map for the flight"""
        # This is a simplified seat map generator
        # In a real system, this would be based on aircraft configuration
        
        aircraft_configs = {
            'Boeing 737': {
                'economy': {'rows': 25, 'seats_per_row': 6, 'start_row': 6},
                'business': {'rows': 4, 'seats_per_row': 4, 'start_row': 1},
            },
            'Airbus A320': {
                'economy': {'rows': 26, 'seats_per_row': 6, 'start_row': 8},
                'business': {'rows': 5, 'seats_per_row': 4, 'start_row': 1},
            },
            'Boeing 777': {
                'economy': {'rows': 32, 'seats_per_row': 9, 'start_row': 15},
                'premium_economy': {'rows': 5, 'seats_per_row': 7, 'start_row': 9},
                'business': {'rows': 6, 'seats_per_row': 6, 'start_row': 1},
            },
        }
        
        # Default configuration if aircraft not found
        aircraft_type = getattr(self.flight, 'aircraft', 'Boeing 737')
        config = aircraft_configs.get(aircraft_type, aircraft_configs['Boeing 737'])
        
        seat_map = {}
        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']
        
        # Generate seats for each class
        for class_type, class_config in config.items():
            seats = []
            start_row = class_config['start_row']
            num_rows = class_config['rows']
            seats_per_row = class_config['seats_per_row']
            
            for row in range(start_row, start_row + num_rows):
                for seat_index in range(seats_per_row):
                    seat_letter = seat_letters[seat_index]
                    seat_number = f"{row}{seat_letter}"
                    
                    # Determine seat characteristics
                    characteristics = []
                    if seat_index == 0:  # First seat in row
                        characteristics.append(SeatCharacteristic.WINDOW)
                    elif seat_index == seats_per_row - 1:  # Last seat in row
                        characteristics.append(SeatCharacteristic.AISLE)
                    elif seat_index == 1 or seat_index == seats_per_row - 2:  # Adjacent to aisle/window
                        if seats_per_row > 4:
                            characteristics.append(SeatCharacteristic.AISLE if seat_index > seats_per_row // 2 else SeatCharacteristic.WINDOW)
                    else:
                        characteristics.append(SeatCharacteristic.MIDDLE)
                    
                    # Exit rows (arbitrary selection for demo)
                    if row in [12, 13, 26, 27]:
                        characteristics.append(SeatCharacteristic.EXIT_ROW)
                    
                    # Bulkhead rows (first row of each section)
                    if row == start_row:
                        characteristics.append(SeatCharacteristic.BULKHEAD)
                    
                    seats.append({
                        'number': seat_number,
                        'row': row,
                        'letter': seat_letter,
                        'type': class_type,
                        'characteristics': characteristics,
                        'status': SeatStatus.AVAILABLE,
                        'price': self._get_seat_price(class_type, characteristics)
                    })
            
            seat_map[class_type] = seats
        
        return seat_map
    
    def _get_seat_price(self, class_type, characteristics):
        """Calculate additional price for seat selection"""
        base_prices = {
            SeatType.ECONOMY: 0,
            SeatType.PREMIUM_ECONOMY: 15,
            SeatType.BUSINESS: 0,
            SeatType.FIRST: 0,
        }
        
        characteristic_prices = {
            SeatCharacteristic.EXIT_ROW: 25,
            SeatCharacteristic.BULKHEAD: 15,
            SeatCharacteristic.PREMIUM: 35,
        }
        
        price = base_prices.get(class_type, 0)
        
        for char in characteristics:
            price += characteristic_prices.get(char, 0)
        
        return Decimal(str(price))
    
    def get_occupied_seats(self):
        """Get list of occupied seats for this flight"""
        occupied_seats = []
        
        # Get all confirmed bookings for this flight
        bookings = Booking.objects.filter(
            flight=self.flight,
            status__in=['confirmed', 'pending']
        ).prefetch_related('passengers')
        
        for booking in bookings:
            for passenger in booking.passengers.all():
                if passenger.assigned_seat:
                    occupied_seats.append(passenger.assigned_seat)
        
        return occupied_seats
    
    def get_available_seats(self, cabin_class):
        """Get available seats for a specific cabin class"""
        occupied_seats = self.get_occupied_seats()
        available_seats = []
        
        if cabin_class in self.seat_map:
            for seat in self.seat_map[cabin_class]:
                if seat['number'] not in occupied_seats:
                    seat['status'] = SeatStatus.AVAILABLE
                    available_seats.append(seat)
                else:
                    seat['status'] = SeatStatus.OCCUPIED
        
        return available_seats
    
    def get_seat_map_json(self, cabin_class=None):
        """Get seat map as JSON for frontend"""
        if cabin_class:
            seats = self.get_available_seats(cabin_class)
            return json.dumps(seats)
        
        full_map = {}
        for class_type in self.seat_map:
            full_map[class_type] = self.get_available_seats(class_type)
        
        return json.dumps(full_map)
    
    def assign_seat(self, passenger, seat_number):
        """Assign a seat to a passenger"""
        # Validate seat availability
        cabin_class = passenger.booking.cabin_class
        available_seats = self.get_available_seats(cabin_class)
        
        seat_found = None
        for seat in available_seats:
            if seat['number'] == seat_number:
                seat_found = seat
                break
        
        if not seat_found:
            raise ValidationError(f"Seat {seat_number} is not available")
        
        # Check if seat is in the correct class
        if seat_found['type'] != cabin_class:
            raise ValidationError(f"Seat {seat_number} is not in {cabin_class} class")
        
        # Assign the seat
        passenger.assigned_seat = seat_number
        passenger.save()
        
        return seat_found
    
    def release_seat(self, passenger):
        """Release a passenger's assigned seat"""
        passenger.assigned_seat = ''
        passenger.save()


class MealPreferenceManager:
    """Manager for meal preferences"""
    
    MEAL_TYPES = [
        ('standard', 'Standard Meal'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('kosher', 'Kosher'),
        ('halal', 'Halal'),
        ('gluten_free', 'Gluten Free'),
        ('diabetic', 'Diabetic'),
        ('low_sodium', 'Low Sodium'),
        ('child_meal', 'Child Meal'),
        ('baby_meal', 'Baby Meal'),
        ('fruit_plate', 'Fresh Fruit Plate'),
        ('seafood', 'Seafood Meal'),
        ('hindu', 'Hindu Meal'),
        ('jain', 'Jain Meal'),
    ]
    
    DIETARY_RESTRICTIONS = [
        ('none', 'No Restrictions'),
        ('nut_allergy', 'Nut Allergy'),
        ('dairy_free', 'Dairy Free'),
        ('egg_free', 'Egg Free'),
        ('shellfish_allergy', 'Shellfish Allergy'),
        ('soy_free', 'Soy Free'),
        ('wheat_free', 'Wheat Free'),
        ('lactose_intolerant', 'Lactose Intolerant'),
    ]
    
    @classmethod
    def get_available_meals(cls, flight_duration_hours=None):
        """Get available meal options based on flight duration"""
        if flight_duration_hours and flight_duration_hours < 2:
            # Short flights - limited options
            return [
                ('standard', 'Snack Box'),
                ('vegetarian', 'Vegetarian Snack'),
                ('fruit_plate', 'Fresh Fruit'),
            ]
        
        return cls.MEAL_TYPES
    
    @classmethod
    def validate_meal_combination(cls, meal_type, dietary_restrictions):
        """Validate meal type and dietary restriction combination"""
        # Some basic validation logic
        if meal_type in ['vegan'] and 'dairy_free' not in dietary_restrictions:
            dietary_restrictions.append('dairy_free')
        
        if meal_type == 'kosher' and 'halal' in [r for r in dietary_restrictions]:
            raise ValidationError("Cannot combine Kosher and Halal requirements")
        
        return dietary_restrictions


class SpecialAssistanceManager:
    """Manager for special assistance requests"""
    
    ASSISTANCE_TYPES = [
        ('wheelchair_ramp', 'Wheelchair - Ramp Access'),
        ('wheelchair_cabin', 'Wheelchair - Can Walk to Cabin'),
        ('wheelchair_onboard', 'Wheelchair - Onboard'),
        ('visual_impairment', 'Visual Impairment Assistance'),
        ('hearing_impairment', 'Hearing Impairment Assistance'),
        ('mobility_assistance', 'General Mobility Assistance'),
        ('oxygen_concentrator', 'Oxygen Concentrator'),
        ('service_animal', 'Service Animal'),
        ('extra_legroom', 'Extra Legroom Required'),
        ('stretcher', 'Stretcher Service'),
        ('unaccompanied_minor', 'Unaccompanied Minor'),
        ('infant_assistance', 'Infant Care Assistance'),
    ]
    
    MEDICAL_CONDITIONS = [
        ('diabetes', 'Diabetes'),
        ('heart_condition', 'Heart Condition'),
        ('respiratory', 'Respiratory Issues'),
        ('epilepsy', 'Epilepsy'),
        ('pregnancy', 'Pregnancy'),
        ('recent_surgery', 'Recent Surgery'),
        ('blood_pressure', 'Blood Pressure Issues'),
        ('anxiety_disorder', 'Anxiety/Panic Disorder'),
    ]
    
    @classmethod
    def validate_assistance_request(cls, assistance_types, medical_conditions, flight):
        """Validate special assistance request"""
        errors = []
        
        # Check for conflicting requests
        if 'stretcher' in assistance_types and len(assistance_types) > 1:
            errors.append("Stretcher service cannot be combined with other assistance types")
        
        # Check flight duration for certain services
        if flight and hasattr(flight, 'duration_minutes'):
            if flight.duration_minutes < 60 and 'oxygen_concentrator' in assistance_types:
                errors.append("Oxygen concentrator not available on flights under 1 hour")
        
        # Medical condition validations
        if 'oxygen_concentrator' in assistance_types and 'respiratory' not in medical_conditions:
            errors.append("Respiratory condition must be declared for oxygen concentrator")
        
        if errors:
            raise ValidationError(errors)
        
        return True
    
    @classmethod
    def get_required_documentation(cls, assistance_types, medical_conditions):
        """Get list of required documentation"""
        docs = []
        
        if any(assist in assistance_types for assist in ['oxygen_concentrator', 'stretcher']):
            docs.append("Medical Certificate (MEDIF form)")
        
        if 'service_animal' in assistance_types:
            docs.append("Service Animal Documentation")
            docs.append("Vaccination Records")
        
        if any(condition in medical_conditions for condition in ['heart_condition', 'recent_surgery']):
            docs.append("Doctor's Clearance Letter")
        
        return docs


class BookingModificationManager:
    """Manager for booking modifications"""
    
    MODIFIABLE_FIELDS = {
        'passenger_details': ['first_name', 'middle_name', 'last_name', 'title'],
        'meal_preferences': ['meal_preference'],
        'seat_assignment': ['assigned_seat'],
        'special_assistance': ['special_assistance'],
        'contact_info': ['email', 'phone'],
    }
    
    @classmethod
    def can_modify_booking(cls, booking, modification_type):
        """Check if a booking can be modified"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Basic rules
        if booking.status == 'cancelled':
            return False, "Cancelled bookings cannot be modified"
        
        # Time-based restrictions
        now = timezone.now()
        departure_time = booking.flight.departure_time
        time_until_departure = departure_time - now
        
        # No modifications within 2 hours of departure
        if time_until_departure < timedelta(hours=2):
            return False, "Modifications not allowed within 2 hours of departure"
        
        # Seat changes not allowed within 24 hours for international flights
        if modification_type == 'seat_assignment':
            hours_limit = 24 if booking.flight.is_international else 4
            if time_until_departure < timedelta(hours=hours_limit):
                return False, f"Seat changes not allowed within {hours_limit} hours of departure"
        
        # Name changes have stricter rules
        if modification_type == 'passenger_details':
            if time_until_departure < timedelta(hours=48):
                return False, "Name changes not allowed within 48 hours of departure"
        
        return True, "Modification allowed"
    
    @classmethod
    def calculate_modification_fee(cls, booking, modification_type):
        """Calculate fees for booking modifications"""
        fees = {
            'passenger_details': Decimal('50.00'),  # Name change fee
            'seat_assignment': Decimal('25.00'),    # Seat change fee
            'meal_preferences': Decimal('0.00'),    # Free
            'special_assistance': Decimal('0.00'),  # Free
            'contact_info': Decimal('0.00'),        # Free
        }
        
        base_fee = fees.get(modification_type, Decimal('0.00'))
        
        # Reduce fees for premium cabin classes
        if booking.cabin_class in ['business', 'first_class']:
            base_fee = base_fee * Decimal('0.5')  # 50% discount
        
        return base_fee