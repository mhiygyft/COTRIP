from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import TransportBooking, TransportStation


class TransportSearchForm(forms.Form):
    TYPE_CHOICES = [
        ('train', 'Tau hoa'),
        ('bus', 'Xe khach'),
    ]

    transport_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        initial='train',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    origin = forms.ModelChoiceField(
        queryset=TransportStation.objects.none(),
        empty_label='Chon diem di',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    destination = forms.ModelChoiceField(
        queryset=TransportStation.objects.none(),
        empty_label='Chon diem den',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    departure_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'min': date.today().isoformat()}),
    )
    passengers = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    seat_class = forms.ChoiceField(
        choices=[
            ('', 'Tat ca hang ghe'),
            ('standard', 'Pho thong'),
            ('sleeper', 'Giuong nam'),
            ('vip', 'Limousine/VIP'),
            ('soft_seat', 'Ghe mem'),
            ('soft_sleeper', 'Giuong nam mem'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stations = TransportStation.objects.filter(is_active=True, is_popular=True).order_by('city', 'name')
        self.fields['origin'].queryset = stations
        self.fields['destination'].queryset = stations

    def clean(self):
        cleaned = super().clean()
        origin = cleaned.get('origin')
        destination = cleaned.get('destination')
        departure_date = cleaned.get('departure_date')

        if origin and destination and origin == destination:
            raise ValidationError('Diem di va diem den phai khac nhau.')
        if departure_date and departure_date < date.today():
            raise ValidationError('Ngay di khong duoc nam trong qua khu.')

        return cleaned


class TransportPassengerForm(forms.ModelForm):
    class Meta:
        model = TransportBooking
        fields = [
            'contact_name',
            'contact_phone',
            'contact_email',
            'pickup_location',
            'dropoff_location',
            'special_requests',
        ]
        widgets = {
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ho va ten'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'So dien thoai'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'pickup_location': forms.Select(attrs={'class': 'form-select'}),
            'dropoff_location': forms.Select(attrs={'class': 'form-select'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Yeu cau them neu co'}),
        }

    def __init__(self, trip=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if trip:
            self.fields['pickup_location'].queryset = TransportStation.objects.filter(
                city=trip.route.origin.city,
                is_active=True,
            ).order_by('name')
            self.fields['dropoff_location'].queryset = TransportStation.objects.filter(
                city=trip.route.destination.city,
                is_active=True,
            ).order_by('name')
        self.fields['pickup_location'].required = False
        self.fields['dropoff_location'].required = False
        self.fields['special_requests'].required = False


class TransportPaymentForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[
            ('bank_transfer', 'Chuyen khoan ngan hang'),
            ('card', 'The tin dung / ghi no'),
            ('cash', 'Thanh toan khi nhan ve'),
            ('skip', 'Thanh toan demo'),
        ],
        initial='bank_transfer',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='Toi dong y voi dieu khoan dat ve',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


def calculate_transport_price(trip, passengers):
    base_price = Decimal(str(trip.base_price)) * Decimal(passengers)
    service_fee = (base_price * Decimal('0.05')).quantize(Decimal('1'))
    total_price = base_price + service_fee
    return base_price, service_fee, total_price
