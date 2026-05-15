import re
from datetime import date, timedelta
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Passenger, Booking, BookingPayment
from .seat_management import (
    SeatMap, MealPreferenceManager, SpecialAssistanceManager,
    BookingModificationManager
)

User = get_user_model()


class PassengerForm(forms.ModelForm):
    """Form for individual passenger information"""
    
    class Meta:
        model = Passenger
        fields = [
            'title', 'first_name', 'middle_name', 'last_name', 'date_of_birth',
            'passenger_type', 'passport_number', 'passport_country', 'passport_expiry',
            'national_id', 'email', 'phone', 'meal_preference', 'seat_preference',
            'special_assistance'
        ]
        
        widgets = {
            'title': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'required': True
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'passenger_type': forms.Select(attrs={'class': 'form-select'}),
            'passport_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter passport number'
            }),
            'passport_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country code (e.g., US, GB)',
                'maxlength': 2
            }),
            'passport_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'National ID (for domestic flights)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'passenger@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 234 567 8900'
            }),
            'meal_preference': forms.Select(attrs={'class': 'form-select'}),
            'seat_preference': forms.Select(attrs={'class': 'form-select'}),
            'special_assistance': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special assistance needed (wheelchair, visual aid, etc.)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.flight = kwargs.pop('flight', None)
        super().__init__(*args, **kwargs)

        required_fields = ['first_name', 'last_name', 'email', 'phone']
        optional_fields = [
            'title', 'middle_name', 'date_of_birth', 'passenger_type',
            'passport_number', 'passport_country', 'passport_expiry',
            'national_id', 'meal_preference', 'seat_preference',
            'special_assistance',
        ]
        for field_name in required_fields:
            self.fields[field_name].required = True
            self.fields[field_name].widget.attrs['required'] = True
        for field_name in optional_fields:
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs.pop('required', None)
        
        # Set date limits
        today = date.today()
        self.fields['date_of_birth'].widget.attrs['max'] = today.strftime('%Y-%m-%d')
        
        # Passport expiry should be in the future
        if self.flight:
            travel_date = self.flight.departure_time.date()
            # Passport should be valid for at least 6 months after travel
            min_expiry = travel_date + timedelta(days=180)
            self.fields['passport_expiry'].widget.attrs['min'] = min_expiry.strftime('%Y-%m-%d')
    
    def clean_passport_country(self):
        country = self.cleaned_data.get('passport_country', '').upper()
        if country and len(country) != 2:
            raise ValidationError("Country code must be 2 characters (e.g., US, GB)")
        return country
    
    def clean_passport_number(self):
        passport_number = self.cleaned_data.get('passport_number', '').strip().upper()
        if passport_number and not re.match(r'^[A-Z0-9]+$', passport_number):
            raise ValidationError("Passport number should contain only letters and numbers")
        return passport_number
    
    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        passenger_type = cleaned_data.get('passenger_type')
        
        # Validate passenger type based on age
        if date_of_birth and passenger_type and self.flight:
            travel_date = self.flight.departure_time.date()
            age = travel_date.year - date_of_birth.year
            
            if travel_date.month < date_of_birth.month or \
               (travel_date.month == date_of_birth.month and travel_date.day < date_of_birth.day):
                age -= 1
            
            if passenger_type == 'infant' and age >= 2:
                raise ValidationError("Infant passengers must be under 2 years old at time of travel")
            elif passenger_type == 'child' and (age < 2 or age >= 12):
                raise ValidationError("Child passengers must be between 2-11 years old at time of travel")
            elif passenger_type == 'adult' and age < 12:
                raise ValidationError("Adult passengers must be 12+ years old at time of travel")
        
        return cleaned_data


class BookingContactForm(forms.ModelForm):
    """Form for booking contact information"""
    
    class Meta:
        model = Booking
        fields = ['contact_email', 'contact_phone', 'special_requests']
        
        widgets = {
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@example.com',
                'required': True
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 234 567 8900',
                'required': True
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Any special requests or additional information...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact_email'].required = True
        self.fields['contact_phone'].required = True
        self.fields['special_requests'].required = False


class PaymentForm(forms.Form):
    """Form for payment information with skip payment option"""
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'The tin dung / ghi no'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Chuyen khoan ngan hang'),
        ('skip', 'Thanh toan demo / bo qua thanh toan'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        initial='card',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Credit card fields
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'pattern': r'[0-9\s]{13,19}',
            'maxlength': 19
        })
    )
    
    card_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name on card'
        })
    )
    
    card_expiry_month = forms.ChoiceField(
        choices=[(i, f"{i:02d}") for i in range(1, 13)],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    card_expiry_year = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(date.today().year, date.today().year + 11)],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    card_cvv = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'pattern': r'[0-9]{3,4}',
            'maxlength': 4
        })
    )
    
    # Billing address
    billing_address = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Billing address'
        })
    )
    
    billing_city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    billing_country = forms.CharField(
        max_length=2,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country (e.g., US)',
            'maxlength': 2
        })
    )
    
    billing_postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal code'
        })
    )
    
    # Terms and conditions
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="I accept the terms and conditions"
    )
    
    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number', '').replace(' ', '')
        if card_number and not self.validate_luhn(card_number):
            raise ValidationError("Please enter a valid card number")
        return card_number
    
    def validate_luhn(self, card_number):
        """Basic Luhn algorithm for card validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    
    def clean_card_cvv(self):
        cvv = self.cleaned_data.get('card_cvv', '')
        if cvv and not re.match(r'^\d{3,4}$', cvv):
            raise ValidationError("CVV must be 3 or 4 digits")
        return cvv
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        return cleaned_data


class BookingSearchForm(forms.Form):
    """Form to search existing bookings"""
    
    booking_reference = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter booking reference (e.g., ABC123)',
            'style': 'text-transform: uppercase'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    
    def clean_booking_reference(self):
        reference = self.cleaned_data.get('booking_reference', '').upper().strip()
        if reference and not re.match(r'^[A-Z0-9]{6}$', reference):
            raise ValidationError("Booking reference should be 6 alphanumeric characters")
        return reference


class CancellationForm(forms.Form):
    """Form for booking cancellation"""
    
    CANCELLATION_REASON_CHOICES = [
        ('change_of_plans', 'Change of plans'),
        ('emergency', 'Emergency'),
        ('illness', 'Illness'),
        ('work', 'Work/Business reasons'),
        ('family', 'Family reasons'),
        ('other', 'Other'),
    ]
    
    reason = forms.ChoiceField(
        choices=CANCELLATION_REASON_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide additional details about your cancellation...'
        }),
        required=False
    )
    
    confirm_cancellation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="I confirm that I want to cancel this booking"
    )


class SeatSelectionForm(forms.Form):
    """Form for seat selection"""
    
    selected_seat = forms.CharField(
        max_length=5,
        widget=forms.HiddenInput(),
        required=False
    )
    
    passenger = forms.ModelChoiceField(
        queryset=Passenger.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    def __init__(self, booking, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        self.fields['passenger'].queryset = booking.passengers.all()
    
    def clean_selected_seat(self):
        seat = self.cleaned_data.get('selected_seat')
        if not seat:
            raise ValidationError("Please select a seat")
        
        # Validate seat availability
        seat_map = SeatMap(self.booking.flight)
        available_seats = seat_map.get_available_seats(self.booking.cabin_class)
        
        seat_available = any(s['number'] == seat for s in available_seats)
        if not seat_available:
            raise ValidationError(f"Seat {seat} is not available")
        
        return seat


class MealPreferenceForm(forms.ModelForm):
    """Form for meal preference selection"""
    
    meal_preference = forms.ChoiceField(
        choices=MealPreferenceManager.MEAL_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    dietary_restrictions = forms.MultipleChoiceField(
        choices=MealPreferenceManager.DIETARY_RESTRICTIONS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    special_meal_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special meal requirements or notes...'
        }),
        required=False
    )
    
    class Meta:
        model = Passenger
        fields = ['meal_preference']
    
    def __init__(self, flight=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if flight:
            # Adjust meal options based on flight duration
            duration_hours = getattr(flight, 'duration_minutes', 120) / 60
            available_meals = MealPreferenceManager.get_available_meals(duration_hours)
            self.fields['meal_preference'].choices = [('', 'Standard Meal')] + available_meals
    
    def clean(self):
        cleaned_data = super().clean()
        meal_type = cleaned_data.get('meal_preference')
        dietary_restrictions = cleaned_data.get('dietary_restrictions', [])
        
        if meal_type and dietary_restrictions:
            try:
                MealPreferenceManager.validate_meal_combination(meal_type, dietary_restrictions)
            except ValidationError as e:
                raise ValidationError(e.message)
        
        return cleaned_data


class SpecialAssistanceForm(forms.Form):
    """Form for special assistance requests"""
    
    assistance_types = forms.MultipleChoiceField(
        choices=SpecialAssistanceManager.ASSISTANCE_TYPES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    medical_conditions = forms.MultipleChoiceField(
        choices=SpecialAssistanceManager.MEDICAL_CONDITIONS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    special_assistance_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide details about your assistance requirements...'
        }),
        required=False
    )
    
    emergency_contact_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    emergency_contact_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    def __init__(self, flight=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flight = flight
    
    def clean(self):
        cleaned_data = super().clean()
        assistance_types = cleaned_data.get('assistance_types', [])
        medical_conditions = cleaned_data.get('medical_conditions', [])
        
        if assistance_types and self.flight:
            try:
                SpecialAssistanceManager.validate_assistance_request(
                    assistance_types, medical_conditions, self.flight
                )
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        # Require emergency contact for certain assistance types
        high_risk_assistance = ['stretcher', 'oxygen_concentrator', 'medical_assistance']
        if any(assist in assistance_types for assist in high_risk_assistance):
            if not cleaned_data.get('emergency_contact_name') or not cleaned_data.get('emergency_contact_phone'):
                raise ValidationError("Emergency contact is required for medical assistance requests")
        
        return cleaned_data


class BookingModificationForm(forms.Form):
    """Form for modifying existing bookings"""
    
    MODIFICATION_TYPE_CHOICES = [
        ('passenger_details', 'Passenger Details'),
        ('meal_preferences', 'Meal Preferences'),
        ('seat_assignment', 'Seat Assignment'),
        ('special_assistance', 'Special Assistance'),
        ('contact_info', 'Contact Information'),
    ]
    
    modification_type = forms.ChoiceField(
        choices=MODIFICATION_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    passenger = forms.ModelChoiceField(
        queryset=Passenger.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    modification_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for modification...'
        }),
        required=False
    )
    
    accept_charges = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I accept any applicable modification charges"
    )
    
    def __init__(self, booking, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        self.fields['passenger'].queryset = booking.passengers.all()
    
    def clean(self):
        cleaned_data = super().clean()
        modification_type = cleaned_data.get('modification_type')
        
        if modification_type:
            # Check if modification is allowed
            can_modify, message = BookingModificationManager.can_modify_booking(
                self.booking, modification_type
            )
            
            if not can_modify:
                raise ValidationError(f"Modification not allowed: {message}")
            
            # Calculate and display fees
            fee = BookingModificationManager.calculate_modification_fee(
                self.booking, modification_type
            )
            
            if fee > 0 and not cleaned_data.get('accept_charges'):
                raise ValidationError(
                    f"This modification incurs a fee of ${fee}. Please accept the charges to proceed."
                )
        
        return cleaned_data


class PassengerDetailsModificationForm(forms.ModelForm):
    """Form for modifying passenger details"""
    
    class Meta:
        model = Passenger
        fields = ['title', 'first_name', 'middle_name', 'last_name']
        widgets = {
            'title': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        if not first_name or not last_name:
            raise ValidationError("First name and last name are required")
        
        return cleaned_data


class ContactInfoModificationForm(forms.ModelForm):
    """Form for modifying contact information"""
    
    class Meta:
        model = Booking
        fields = ['contact_email', 'contact_phone']
        widgets = {
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BookingTimelineForm(forms.Form):
    """Form for viewing booking timeline and status"""
    
    show_all_events = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Show all events"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
