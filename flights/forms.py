from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Airline, Airport, Flight, FlightSearch


class FlightSearchForm(forms.Form):
    TRIP_TYPE_CHOICES = [
        ('round_trip', 'Round Trip'),
        ('one_way', 'One Way'),
        ('multi_city', 'Multi City'),
    ]
    
    CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first_class', 'First Class'),
    ]
    
    PASSENGER_CHOICES = [(i, str(i)) for i in range(1, 10)]
    
    trip_type = forms.ChoiceField(
        choices=TRIP_TYPE_CHOICES,
        initial='round_trip',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
    
    origin = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_popular=True).order_by('name'),
        empty_label="Select departure airport",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'From where?'
        })
    )
    
    destination = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_popular=True).order_by('name'),
        empty_label="Select destination airport",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Where to?'
        })
    )
    
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().strftime('%Y-%m-%d')
        })
    )
    
    return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().strftime('%Y-%m-%d')
        })
    )
    
    passengers = forms.ChoiceField(
        choices=PASSENGER_CHOICES,
        initial=1,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    cabin_class = forms.ChoiceField(
        choices=CLASS_CHOICES,
        initial='economy',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        departure_date = cleaned_data.get('departure_date')
        return_date = cleaned_data.get('return_date')
        trip_type = cleaned_data.get('trip_type')
        
        # Check that origin and destination are different
        if origin and destination and origin == destination:
            raise ValidationError("Origin and destination airports must be different.")
        
        # Check departure date is not in the past
        if departure_date and departure_date < date.today():
            raise ValidationError("Departure date cannot be in the past.")
        
        # For round trip, return date is required and must be after departure
        if trip_type == 'round_trip':
            if not return_date:
                raise ValidationError("Return date is required for round trip flights.")
            elif departure_date and return_date and return_date <= departure_date:
                raise ValidationError("Return date must be after departure date.")
        
        return cleaned_data


class FlightFilterForm(forms.Form):
    SORT_CHOICES = [
        ('departure_time', 'Departure Time'),
        ('arrival_time', 'Arrival Time'),
        ('duration', 'Duration'),
        ('price_low_high', 'Price: Low to High'),
        ('price_high_low', 'Price: High to Low'),
    ]
    
    STOPS_CHOICES = [
        ('', 'Any number of stops'),
        ('0', 'Non-stop'),
        ('1', '1 stop'),
        ('2+', '2+ stops'),
    ]
    
    TIME_CHOICES = [
        ('', 'Any time'),
        ('morning', 'Morning (6:00 - 12:00)'),
        ('afternoon', 'Afternoon (12:00 - 18:00)'),
        ('evening', 'Evening (18:00 - 24:00)'),
        ('late_night', 'Late Night (0:00 - 6:00)'),
    ]
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='price_low_high',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    airlines = forms.ModelMultipleChoiceField(
        queryset=Airline.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    stops = forms.ChoiceField(
        choices=STOPS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    departure_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    arrival_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Min price'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Max price'
        })
    )
    
    def __init__(self, *args, airlines_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['airlines'].queryset = airlines_queryset or Airline.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price >= max_price:
            raise ValidationError("Maximum price must be greater than minimum price.")
        
        return cleaned_data


class FlightSearchSaveForm(forms.ModelForm):
    """Form to save flight searches for logged-in users"""
    
    class Meta:
        model = FlightSearch
        fields = ['search_name']
        widgets = {
            'search_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a name for this search...',
                'maxlength': 100
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class QuickFlightSearchForm(forms.Form):
    """Simplified search form for homepage/navigation"""
    
    origin = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'From',
            'list': 'airports-list'
        })
    )
    
    destination = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'To',
            'list': 'airports-list'
        })
    )
    
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': date.today().strftime('%Y-%m-%d')
        })
    )
    
    def clean_origin(self):
        origin = self.cleaned_data.get('origin', '').upper()
        try:
            airport = Airport.objects.get(iata_code=origin)
            return airport
        except Airport.DoesNotExist:
            raise ValidationError("Please select a valid departure airport.")
    
    def clean_destination(self):
        destination = self.cleaned_data.get('destination', '').upper()
        try:
            airport = Airport.objects.get(iata_code=destination)
            return airport
        except Airport.DoesNotExist:
            raise ValidationError("Please select a valid destination airport.")
    
    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        
        if origin and destination and origin == destination:
            raise ValidationError("Origin and destination must be different.")
        
        return cleaned_data
